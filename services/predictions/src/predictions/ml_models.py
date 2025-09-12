import os
import mlflow
import optuna
import numpy as np
import pandas as pd
from loguru import logger
from typing import Optional
from sklearn.pipeline import Pipeline
from lazypredict.Supervised import LazyRegressor
from sklearn.linear_model import HuberRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import StandardScaler

from predictions.constants import (
    DEFAULT_HYPERPARAM_SPLITS,
    HUBER_EPSILON_MIN,
    HUBER_EPSILON_MAX,
    HUBER_ALPHA_MIN,
    HUBER_ALPHA_MAX,
    HUBER_MAX_ITER_MIN,
    HUBER_MAX_ITER_MAX,
    HUBER_TOL_MIN,
    HUBER_TOL_MAX,
)
from predictions.models.exceptions import ModelError


class BaselineModel:
    def __init__(self):
        """
        Provide initial parameters to initialize the model.
        """
        pass

    def fit(self, X, y):
        """
        Fit the model to the data.
        """
        pass

    def predict(self, X) -> pd.Series:
        """
        Predict the target variable.
        """
        return X['close']


# Define a custom type that can be either a string or a HuberRegressorWithHyperparameterTuning
# Model = Union[HuberRegressorWithHyperparameterTuning]


def get_best_model_candidate(model_candidates_from_best_to_worst: list[str]) -> 'HuberRegressorWithHyperparameterTuning':
    """
    Factory function that returns a model from the given list of model candidates.
    It returns the first model that is found, which means the best model candidate.

    Args:
        model_candidates_from_best_to_worst: list[str], the list of model candidates from best to worst

    Returns:
        Model, the model
    """

    def _get_one_model(model_name: str):
        if model_name == 'HuberRegressor':
            return HuberRegressorWithHyperparameterTuning()
        else:
            raise ModelError(f'Model {model_name} not found')

    model = None
    for model_name in model_candidates_from_best_to_worst:
        try:
            model = _get_one_model(model_name)
            break
        except ModelError as e:
            logger.error(f'Model {model_name} not found: {e}')
            continue

    # TODO: we probably need to handle the edge case where no model is found

    return model


class HuberRegressorWithHyperparameterTuning:
    """
    Fits a HuberRegressor with hyperparameter tuning.
    """

    def __init__(
        self,
        # hyperparam_search_trials: Optional[int] = 0,
        # hyperparam_splits: Optional[int] = 3
    ):
        """
        Initialize the model.
        """
        self.pipeline = self._get_pipeline()
        self.hyperparam_search_trials = None
        self.hyperparam_splits = None

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        hyperparam_search_trials: Optional[int] = 0,
        hyperparam_splits: Optional[int] = DEFAULT_HYPERPARAM_SPLITS,
    ):
        """
        Fit the model to the data, possibly with hyperparameter tuning.

        Args:
            X: pd.DataFrame, the training data
            y: pd.Series, the target variable
        """
        self.hyperparam_search_trials = hyperparam_search_trials
        self.hyperparam_splits = hyperparam_splits

        if self.hyperparam_search_trials == 0:
            logger.info(
                'No hyperparam search trials provided, fitting the model with default hyperparameters'
            )
            self.pipeline.fit(X, y)

        else:
            logger.info(
                f"Let's find the best hyperparams for the model with {self.hyperparam_search_trials} trials"
            )
            best_hyperparams = self._find_best_hyperparams(X, y)
            logger.info(f'Best hyperparams: {best_hyperparams}')
            self.pipeline = self._get_pipeline(best_hyperparams)
            logger.info('Fitting the model with the best hyperparams')
            self.pipeline.fit(X, y)

    def _get_pipeline(self, model_hyperparams: Optional[dict] = None) -> Pipeline:
        """
        Get the pipeline.
        """
        if model_hyperparams is None:
            pipeline = Pipeline(
                steps=[('preprocessor', StandardScaler()),
                       ('model', HuberRegressor())]
            )
        else:
            pipeline = Pipeline(
                steps=[
                    ('preprocessor', StandardScaler()),
                    ('model', HuberRegressor(**model_hyperparams)),
                ]
            )
        return pipeline

    def predict(self, X: pd.DataFrame) -> pd.Series:
        """
        Predict the target variable.
        """
        return self.pipeline.predict(X)

    def _find_best_hyperparams(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
    ) -> dict:
        """
        Finds the best hyperparameters for the model using Bayesian optimization.

        Args:
            X_train: pd.DataFrame, the training data
            y_train: pd.Series, the target variable

        Returns:
            dict, the best hyperparameters
        """

        def objective(trial: optuna.Trial) -> float:
            """
            Objective function for Optuna that returns the mean absolute error we
            want to minimize.

            Args:
                trial: optuna.Trial, the trial object

            Returns:
                float, the mean absolute error
            """
            # we ask Optuna to sample the next set of hyperparameters for the HuberRegressor
            # these are our candidates for this trial
            params = {
                'epsilon': trial.suggest_float('epsilon', HUBER_EPSILON_MIN, HUBER_EPSILON_MAX),
                'alpha': trial.suggest_float('alpha', HUBER_ALPHA_MIN, HUBER_ALPHA_MAX),
                'max_iter': trial.suggest_int('max_iter', HUBER_MAX_ITER_MIN, HUBER_MAX_ITER_MAX),
                'tol': trial.suggest_float('tol', HUBER_TOL_MIN, HUBER_TOL_MAX),
                'fit_intercept': trial.suggest_categorical(
                    'fit_intercept', [True, False]
                ),
            }

            # let's split our X_train into n_splits folds with a time-series split
            # we want to keep the time-series order in each fold
            # we will use the time-series split from sklearn
            from sklearn.model_selection import TimeSeriesSplit

            tscv = TimeSeriesSplit(n_splits=self.hyperparam_splits)
            mae_scores = []
            for train_index, val_index in tscv.split(X_train):
                # split the data into training and validation sets
                X_train_fold, X_val_fold = (
                    X_train.iloc[train_index],
                    X_train.iloc[val_index],
                )
                y_train_fold, y_val_fold = (
                    y_train.iloc[train_index],
                    y_train.iloc[val_index],
                )

                # build a pipeline with preprocessing and model steps
                self.pipeline = self._get_pipeline(model_hyperparams=params)

                # train the model on the training set
                self.pipeline.fit(X_train_fold, y_train_fold)

                # evaluate the model on the validation set
                y_pred = self.pipeline.predict(X_val_fold)
                mae = mean_absolute_error(y_val_fold, y_pred)
                mae_scores.append(mae)

            # return the average MAE across all folds

            return np.mean(mae_scores)

        # we create a study object that minimizes the objective function
        study = optuna.create_study(direction='minimize')

        # we run the trials
        logger.info(f'Running {self.hyperparam_search_trials} trials')
        study.optimize(objective, n_trials=self.hyperparam_search_trials)

        # we return the best hyperparameters
        return study.best_trial.params


def get_model_candidates(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    n_candidates: int,
) -> list[str]:
    """
    Uses lazypredict to fit N models with default hyperparameters for the given
    (X_train, y_train), and evaluate them with (X_test, y_test)

    It returns a list of model names, from best to worst.

    Args:
        X_train: pd.DataFrame, the training data
        y_train: pd.Series, the target variable
        X_test: pd.DataFrame, the test data
        y_test: pd.Series, the target variable
        n_candidates: int, the number of candidates to return

    Returns:
        list[str], the list of model names from best to worst
    """
    # unset the MLFLOW_TRACKING_URI
    mlflow_tracking_uri = os.environ['MLFLOW_TRACKING_URI']
    del os.environ['MLFLOW_TRACKING_URI']

    # fit N models with default hyperparameters
    reg = LazyRegressor(
        verbose=0, ignore_warnings=False, custom_metric=mean_absolute_error
    )
    models, _ = reg.fit(X_train, X_test, y_train, y_test)

    # reset the index so that the model names are in the first column
    models.reset_index(inplace=True)

    # log table to mlflow experiment
    mlflow.log_table(
        models, 'model_candidates_with_default_hyperparameters.json')

    # set the MLFLOW_TRACKING_URI back to its original value
    os.environ['MLFLOW_TRACKING_URI'] = mlflow_tracking_uri

    # list of top n_candidates model names
    model_candidates = models['Model'].tolist()[:n_candidates]

    return model_candidates


# TODO: create a custom type called Model and use it to annotate things like the output of this function
def get_model_obj(model_name: str) -> 'HuberRegressorWithHyperparameterTuning':
    """
    Factory function that returns a model object from the given model name.
    """
    if model_name == 'HuberRegressor':
        return HuberRegressorWithHyperparameterTuning()
    else:
        raise ModelError(f'Model {model_name} not found')
