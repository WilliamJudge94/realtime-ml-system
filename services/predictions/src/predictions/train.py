"""
The training script for the predictor service.

Has the following steps:
1. Fetch data from RisingWave
2. Add target column
3. Validate the data
4. Profile it
5. Split into train/test
6. Baseline model
7. XGBoost model with default hyperparameters
8. Validate final model
9. Push model
10. Hyperparameter tuning
"""

from typing import Optional

import mlflow
import pandas as pd
from loguru import logger
from risingwave import OutputFormat, RisingWave, RisingWaveConnOptions
from sklearn.metrics import mean_absolute_error

from predictions.data_validation import validate_data
from predictions.model_registry import get_model_name, push_model
from predictions.models import (
    BaselineModel,
    get_model_candidates,
    get_model_obj,
)


def generate_exploratory_data_analysis_report(
    ts_data: pd.DataFrame,
    output_html_path: str,
):
    """
    Genearates an HTML file exploratory data analysis charts for the given `ts_data` and
    saves it locally to the given `output_html_path`

    Args:
        ts_data:
        output_html_file:
    """
    from ydata_profiling import ProfileReport

    profile = ProfileReport(
        ts_data, tsmode=True, sortby='window_start_ms', title='Technical indicators EDA'
    )
    profile.to_file(output_html_path)


def load_ts_data_from_risingwave(
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    table: str,
    pair: str,
    training_data_horizon_days: int,
    candle_seconds: int,
) -> pd.DataFrame:
    """
    Fetches technical indicators data from RisingWave for the given pair and time range.

    Args:
        host: str: The host of the RisingWave instance.
        port: int: The port of the RisingWave instance.
        user: str: The user to connect to RisingWave.
        password: str: The password to connect to RisingWave.
        database: str: The database to connect to RisingWave.
        pair: str: The trading pair to fetch data for.
        training_data_horizon_days: int: The number of days in the past to fetch data for.
        candle_seconds: int: The candle duration in seconds.

    Returns:
        pd.DataFrame: A DataFrame containing the technical indicators data for the given pair.
    """
    logger.info('Establishing connection to RisingWave')
    rw = RisingWave(
        RisingWaveConnOptions.from_connection_info(
            host=host, port=port, user=user, password=password, database=database
        )
    )
    query = f"""
    select
        *
    from
        {table}
    where
        pair='{pair}'
        and candle_seconds='{candle_seconds}'
        and to_timestamp(window_start_ms / 1000) > now() - interval '{training_data_horizon_days} days'
    order by
        window_start_ms;
    """

    ts_data = rw.fetch(query, format=OutputFormat.DATAFRAME)

    logger.info(
        f'Fetched {len(ts_data)} rows of data for {pair} in the last {training_data_horizon_days} days'
    )

    return ts_data


def train(
    mlflow_tracking_uri: str,
    mlflow_tracking_username: str,
    mlflow_tracking_password: str,
    risingwave_host: str,
    risingwave_port: int,
    risingwave_user: str,
    risingwave_password: str,
    risingwave_database: str,
    risingwave_table: str,
    pair: str,
    training_data_horizon_days: int,
    candle_seconds: int,
    prediction_horizon_seconds: int,
    train_test_split_ratio: float,
    max_percentage_rows_with_missing_values: float,
    data_profiling_n_rows: int,
    eda_report_html_path: str,
    features: list[str],
    hyperparam_search_trials: int,
    model_name: Optional[str] = None,
    n_model_candidates: Optional[int] = 1,
    max_percentage_diff_mae_wrt_baseline: Optional[float] = 0.10,
):
    """
    Trains a predictor for the given pair and data, and if the model is good, it pushes
    it to the model registry.
    """
    logger.info('Starting training process')

    logger.info('Setting up MLflow tracking URI and authentication')
    import os
    os.environ['MLFLOW_TRACKING_USERNAME'] = mlflow_tracking_username
    os.environ['MLFLOW_TRACKING_PASSWORD'] = mlflow_tracking_password
    mlflow.set_tracking_uri(mlflow_tracking_uri)

    logger.info('Setting up MLflow experiment')
    mlflow.set_experiment(
        get_model_name(pair, candle_seconds, prediction_horizon_seconds)
    )

    # Things we want to log to MLflow:
    # - The data we used to train the model
    # - Parameters
    # - EDA report
    # - Model performance metrics

    with mlflow.start_run():
        logger.info('Starting MLflow run')

        # Input to the training process
        mlflow.log_param('features', features)
        mlflow.log_param('pair', pair)
        mlflow.log_param('training_data_horizon_days',
                         training_data_horizon_days)
        mlflow.log_param('candle_seconds', candle_seconds)
        mlflow.log_param('prediction_horizon_seconds',
                         prediction_horizon_seconds)
        mlflow.log_param('train_test_split_ratio', train_test_split_ratio)
        mlflow.log_param('data_profiling_n_rows', data_profiling_n_rows)
        if model_name:
            mlflow.log_param('model_name', model_name)
        mlflow.log_param(
            'max_percentage_diff_mae_wrt_baseline', max_percentage_diff_mae_wrt_baseline
        )

        # Step 1. Load technical indicators data from RisingWave
        ts_data = load_ts_data_from_risingwave(
            host=risingwave_host,
            port=risingwave_port,
            user=risingwave_user,
            password=risingwave_password,
            database=risingwave_database,
            table=risingwave_table,
            pair=pair,
            training_data_horizon_days=training_data_horizon_days,
            candle_seconds=candle_seconds,
        )
        # keep only the `features`
        ts_data = ts_data[features]

        # Step 2. Add target column
        ts_data['target'] = ts_data['close'].shift(
            -prediction_horizon_seconds // candle_seconds
        )

        # log the data to MLflow
        dataset = mlflow.data.from_pandas(ts_data)
        mlflow.log_input(dataset, context='training')

        # log dataset size
        mlflow.log_param('ts_data_shape', ts_data.shape)

        # Step 3. Validate the data
        ts_data = validate_data(
            ts_data, max_percentage_rows_with_missing_values)

        # Homework:
        # Plot data drift of the current data vs the data used by the model in the model registry.
        from predictions.data_validation import generate_data_drift_report

        generate_data_drift_report(ts_data, model_name)

        # Step 4. Profile the data
        # after the break
        ts_data_to_profile = (
            ts_data.head(
                data_profiling_n_rows) if data_profiling_n_rows else ts_data
        )
        generate_exploratory_data_analysis_report(
            ts_data_to_profile, output_html_path=eda_report_html_path
        )
        logger.info('Pushing EDA report to MLflow')
        mlflow.log_artifact(local_path=eda_report_html_path,
                            artifact_path='eda_report')

        # Step 5. Split into train/test
        train_size = int(len(ts_data) * train_test_split_ratio)
        train_data = ts_data[:train_size]
        test_data = ts_data[train_size:]
        mlflow.log_param('train_data_shape', train_data.shape)
        mlflow.log_param('test_data_shape', test_data.shape)

        # Step 6. Split data into features and target
        X_train = train_data.drop(columns=['target'])
        y_train = train_data['target']
        X_test = test_data.drop(columns=['target'])
        y_test = test_data['target']
        mlflow.log_param('X_train_shape', X_train.shape)
        mlflow.log_param('y_train_shape', y_train.shape)
        mlflow.log_param('X_test_shape', X_test.shape)
        mlflow.log_param('y_test_shape', y_test.shape)

        # Step 7. Build a dummy baseline model
        baseline_model = BaselineModel()
        y_pred = baseline_model.predict(X_test)
        test_mae_baseline = mean_absolute_error(y_test, y_pred)
        mlflow.log_metric('test_mae_baseline', test_mae_baseline)
        logger.info(f'Test MAE for Baseline model: {test_mae_baseline:.4f}')

        # Step 8. Find the best candidate model, if `model_name` is not provided.
        if model_name is None:
            # We fit N models with default hyperparameters for the given
            # (X_train, y_train), and evaluate them with (X_test, y_test)
            # to find the best `n_model_candidates` models
            model_names = get_model_candidates(
                X_train, y_train, X_test, y_test, n_candidates=n_model_candidates
            )

            # TODO: this is a hack that works when we have only one candidate model
            # How would you modify this code to use a list of candiate models, and adjust
            # their hyperparameters in the next step?
            model_name = model_names[0]

        model = get_model_obj(model_name)

        # Step 9. Train the choosen model with hyperparameter search.
        logger.info(f'Start training model {model} with hyperparameter search')
        model.fit(X_train, y_train,
                  hyperparam_search_trials=hyperparam_search_trials)

        # Step 10. Validate the model
        y_pred = model.predict(X_test)
        test_mae = mean_absolute_error(y_test, y_pred)
        mlflow.log_metric('test_mae', test_mae)
        logger.info(f'Test MAE for model {model}: {test_mae:.4f}')

        # Step 11. Push the model to the model registry
        mae_diff = (test_mae - test_mae_baseline) / test_mae_baseline
        if mae_diff <= max_percentage_diff_mae_wrt_baseline:
            logger.info(
                f'Model MAE is {mae_diff:.4f} < {max_percentage_diff_mae_wrt_baseline}'
            )
            logger.info('Pushing model to the registry')
            model_name = get_model_name(
                pair, candle_seconds, prediction_horizon_seconds
            )
            push_model(model, X_test, model_name)
        else:
            logger.info(
                f'The model {model_name} MAE is {mae_diff:.4f} > {max_percentage_diff_mae_wrt_baseline}'
            )
            logger.info('Model NOT PUSHED to the registry')


if __name__ == '__main__':
    from predictions.config import training_config as config

    train(
        mlflow_tracking_uri=config.mlflow_tracking_uri,
        mlflow_tracking_username=config.mlflow_tracking_username,
        mlflow_tracking_password=config.mlflow_tracking_password,
        risingwave_host=config.risingwave_host,
        risingwave_port=config.risingwave_port,
        risingwave_user=config.risingwave_user,
        risingwave_password=config.risingwave_password,
        risingwave_database=config.risingwave_database,
        risingwave_table=config.risingwave_table,
        pair=config.pair,
        training_data_horizon_days=config.training_data_horizon_days,
        candle_seconds=config.candle_seconds,
        prediction_horizon_seconds=config.prediction_horizon_seconds,
        train_test_split_ratio=config.train_test_split_ratio,
        max_percentage_rows_with_missing_values=config.max_percentage_rows_with_missing_values,
        # TODO: set to 1 to speed up development
        data_profiling_n_rows=config.data_profiling_n_rows,
        eda_report_html_path=config.eda_report_html_path,
        features=config.features,
        hyperparam_search_trials=config.hyperparam_search_trials,
        model_name=config.model_name,
        n_model_candidates=config.n_model_candidates,
        max_percentage_diff_mae_wrt_baseline=config.max_percentage_diff_mae_wrt_baseline,
    )
