from typing import Optional

from pydantic_settings import BaseSettings


class TrainingConfig(BaseSettings):
    mlflow_tracking_uri: str = 'http://localhost:5000'
    mlflow_tracking_username: str = 'user'
    mlflow_tracking_password: str = '6440921D-2493-42AA-BE40-428CD753D81D'
    risingwave_host: str = 'localhost'
    risingwave_port: int = 4567
    risingwave_user: str = 'root'
    risingwave_password: str = ''
    risingwave_database: str = 'dev'
    risingwave_table: str = 'public.technical_indicators'
    pair: str = 'BTC/USD'
    training_data_horizon_days: int = 10
    candle_seconds: int = 60
    prediction_horizon_seconds: int = 300
    train_test_split_ratio: float = 0.8
    max_percentage_rows_with_missing_values: float = 0.01
    data_profiling_n_rows: int = 1
    eda_report_html_path: str = './eda_report.html'
    features: list[str] = [
        'open',
        'high',
        'low',
        'close',
        'window_start_ms',
        'volume',
        'sma_7',
        'sma_14',
        'sma_21',
        'sma_60',
        'ema_7',
        'ema_14',
        'ema_21',
        'ema_60',
        'rsi_7',
        'rsi_14',
        'rsi_21',
        'rsi_60',
        'macd_7',
        'macdsignal_7',
        'macdhist_7',
        'obv',
    ]
    hyperparam_search_trials: int = 5
    model_name: Optional[str] = 'HuberRegressor'
    n_model_candidates: int = 1
    max_percentage_diff_mae_wrt_baseline: float = (
        0.50  # in a real scenario you can reduce this parameter further.
    )


training_config = TrainingConfig()


class PredictorConfig(BaseSettings):
    mlflow_tracking_uri: str = 'http://localhost:5000'
    mlflow_tracking_username: str = 'user'
    mlflow_tracking_password: str = '6440921D-2493-42AA-BE40-428CD753D81D'
    risingwave_host: str = 'localhost'
    risingwave_port: int = 4567
    risingwave_user: str = 'root'
    risingwave_password: str = ''
    risingwave_database: str = 'dev'
    risingwave_schema: str = 'public'
    risingwave_input_table: str = 'technical_indicators'
    risingwave_output_table: str = 'predictions'

    pair: str = 'BTC/USD'
    prediction_horizon_seconds: int = 300
    candle_seconds: int = 60
    model_version: Optional[str] = 'latest'


predictor_config = PredictorConfig()
