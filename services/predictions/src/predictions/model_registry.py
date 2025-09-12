import mlflow
import pandas as pd
from loguru import logger
from mlflow.models import infer_signature
from typing import Any, Optional, Tuple, Protocol


class MLModel(Protocol):
    """Protocol for ML models with predict method."""

    def predict(self, X: pd.DataFrame) -> Any:
        """Predict using the model."""
        ...


def get_model_name(
    pair: str, candle_seconds: int, prediction_horizon_seconds: int
) -> str:
    """
    Returns the model name for the given pair, candle seconds, and prediction horizon
    seconds.
    """
    return f'{pair.replace("/", "-")}_{candle_seconds}_{prediction_horizon_seconds}'


def load_model(
    model_name: str,
    model_version: Optional[str] = 'latest',
) -> Tuple[MLModel, list[str]]:
    """
    Loads the given `model_name` with version `model_version` from the MLflow model registry,
    together with the model's input schema.

    Args:
        model_name: The name of the model to load from the MLflow model registry.
        model_version: The version of the model to load from the MLflow model registry.

    Returns:
        The model object and the model's feature list.

    """
    model = mlflow.sklearn.load_model(
        model_uri=f'models:/{model_name}/{model_version}')

    # Get the model info which contains the signature
    model_info = mlflow.models.get_model_info(
        model_uri=f'models:/{model_name}/{model_version}'
    )

    # Access the signature, and extract the list of model features.
    features = model_info.signature.inputs.input_names()

    return model, features


def push_model(
    model: MLModel,
    X_test: pd.DataFrame,
    model_name: str,
) -> None:
    """
    Pushes the given `model` to the MLflow model registry using the given `model_name`.

    Args:
        model: The model to push to the model registry.
        X_test: The test data to use to infer the model signature.
        model_name: The name of the model to push to the model registry.
    """
    # Infer the model signature
    y_pred = model.predict(X_test)
    signature = infer_signature(X_test, y_pred)

    # Log the sklearn model and register as version 1
    logger.info(f'Pushing model {model_name} to the model registry')
    mlflow.sklearn.log_model(
        sk_model=model,
        artifact_path='model',
        signature=signature,
        registered_model_name=model_name,
    )
    logger.info(f'Model {model_name} pushed to the model registry')
