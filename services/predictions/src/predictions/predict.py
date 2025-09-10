from datetime import datetime, timezone
from typing import Optional

import pandas as pd
from loguru import logger
from risingwave import OutputFormat, RisingWave, RisingWaveConnOptions

from predictions.model_registry import get_model_name, load_model


def predict(
    mlflow_tracking_uri: str,
    risingwave_host: str,
    risingwave_port: int,
    risingwave_user: str,
    risingwave_password: str,
    risingwave_database: str,
    risingwave_schema: str,
    risingwave_input_table: str,
    risingwave_output_table: str,
    pair: str,
    prediction_horizon_seconds: int,
    candle_seconds: int,
    model_version: Optional[str] = 'latest',
):
    """
    Generates a new prediction as soon as new data is available in the `risingwave_input_table`.

    Steps:
    1. Load the model from the MLflow model registry with the given `model_version`, if provided,
    otherwise load the latest model.
    2. Start listening to data changes in the `risingwave_input_table`.
    3. For each new or updated row, generate a prediction.
    4. Write the prediction to the `risingwave_output_table`.

    Args:
        mlflow_tracking_uri: The URI of the MLflow tracking server.
        risingwave_host: The host of the RisingWave server.
        risingwave_port: The port of the RisingWave server.
        risingwave_user: The user of the RisingWave server.
        risingwave_password: The password of the RisingWave server.
        risingwave_database: The database of the RisingWave server.
        risingwave_input_table: The input table of the RisingWave server.
        risingwave_output_table: The output table of the RisingWave server.
        pair: The pair of the asset to predict.
        prediction_horizon_seconds: The prediction horizon in seconds.
        candle_seconds: The candle seconds of the asset to predict.
        model_version: The version of the model to load from the MLflow model registry.
    """
    # Step 1. Load the model from the MLflow model registry
    model_name = get_model_name(
        pair, candle_seconds, prediction_horizon_seconds)
    logger.info(f'Loading model {model_name} with version {model_version}')
    model, features = load_model(model_name, model_version)

    # Step 2. Start listening to data changes in the `risingwave_input_table`
    rw = RisingWave(
        RisingWaveConnOptions.from_connection_info(
            host=risingwave_host,
            port=risingwave_port,
            user=risingwave_user,
            password=risingwave_password,
            database=risingwave_database,
        )
    )

    def prediction_handler(data: pd.DataFrame):
        """
        Maps the given input data changes to fresh predictions using the loaded model.
        These predictions are then written to the `risingwave_output_table`.
        """
        logger.info(
            f'Received {data.shape[0]} updates from {risingwave_input_table}')
        # print(data)

        # Filter only Insert and Updates
        data = data[data['op'].isin(['Insert', 'UpdateInsert'])]

        # for the given `pair`
        data = data[data['pair'] == pair]

        # for the given `candle_seconds`
        data = data[data['candle_seconds'] == candle_seconds]

        # for recent data, because we don't want to
        # score updates for old data coming from our backfill pipeline.
        current_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        data = data[data['window_start_ms'] >
                    current_ms - 1000 * candle_seconds * 2]

        # Keep only the `features` columns in data
        data = data[features]

        # Generate predictions
        if data.empty:
            return

        # Generate predictions
        predictions: pd.Series = model.predict(data)

        # Prepare the output dataframe
        output = pd.DataFrame()
        output['predicted_price'] = predictions
        output['pair'] = pair
        output['ts_ms'] = int(datetime.now(timezone.utc).timestamp() * 1000)
        output['model_name'] = model_name
        output['model_version'] = model_version

        # TODO: remove this hardcoded value
        # For some misterious reason the variable `prediction_horizon_seconds` is not available
        # in the scope of the function `prediction_handler`, while `pair` and `candle_seconds` are.
        # prediction_horizon_seconds = 300
        # breakpoint()

        output['predicted_ts_ms'] = (
            data['window_start_ms']
            + (candle_seconds + prediction_horizon_seconds) * 1000
        ).to_list()

        logger.info(
            f'Writing {len(output)} predictions to table {risingwave_output_table}'
        )

        # Write dataframe to the `risingwave_output_table`
        rw.insert(table_name=risingwave_output_table, data=output)

    rw.on_change(
        subscribe_from=risingwave_input_table,
        schema_name=risingwave_schema,
        handler=prediction_handler,
        output_format=OutputFormat.DATAFRAME,
    )


if __name__ == '__main__':
    from predictor.config import predictor_config as config

    predict(
        mlflow_tracking_uri=config.mlflow_tracking_uri,
        risingwave_host=config.risingwave_host,
        risingwave_port=config.risingwave_port,
        risingwave_user=config.risingwave_user,
        risingwave_password=config.risingwave_password,
        risingwave_database=config.risingwave_database,
        risingwave_schema=config.risingwave_schema,
        risingwave_input_table=config.risingwave_input_table,
        risingwave_output_table=config.risingwave_output_table,
        pair=config.pair,
        prediction_horizon_seconds=config.prediction_horizon_seconds,
        candle_seconds=config.candle_seconds,
        model_version=config.model_version,
    )
