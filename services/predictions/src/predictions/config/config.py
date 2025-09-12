import re
from loguru import logger
from pathlib import Path
from typing import List, Optional
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent / "local.env",
        env_prefix="PREDICTIONS_",
        case_sensitive=False,
    )

    logger.debug(f"Loading settings from {Path(__file__).parent / 'local.env'}")

    # Application settings
    app_name: str = "predictions"
    debug: bool = False
    log_level: str = "INFO"
    log_format: str = "json"

    # Kafka settings
    kafka_broker_address: str = "localhost:9092"
    kafka_input_topic: str = "technical_indicators"
    kafka_output_topic: str = "predictions"
    kafka_consumer_group: str = "predictions_consumer_group"

    # Processing settings
    candle_seconds: int = 60
    processing_mode: str = "live"
    pair: str = "BTC/USD"

    # Model settings
    model_name: str = "HuberRegressor"
    model_version: str = "latest"
    prediction_horizon_seconds: int = 300

    # MLflow settings
    mlflow_tracking_uri: str = "http://localhost:5000"
    mlflow_tracking_username: str = "user"
    mlflow_tracking_password: str = "6440921D-2493-42AA-BE40-428CD753D81D"

    # Database settings
    risingwave_host: str = "localhost"
    risingwave_port: int = 4567
    risingwave_user: str = "root"
    risingwave_password: str = ""
    risingwave_database: str = "dev"
    risingwave_schema: str = "public"
    risingwave_input_table: str = "technical_indicators"
    risingwave_output_table: str = "predictions"

    # Training specific settings
    training_data_horizon_days: int = 10
    train_test_split_ratio: float = 0.8
    max_percentage_rows_with_missing_values: float = 0.01
    data_profiling_n_rows: int = 700
    eda_report_html_path: str = "./eda_report.html"
    training_plots_path: str = "./training_data_plots.png"
    hyperparam_search_trials: int = 5
    n_model_candidates: int = 1
    max_percentage_diff_mae_wrt_baseline: float = 0.50

    # Feature settings
    features: List[str] = [
        "open",
        "high", 
        "low",
        "close",
        "window_start_ms",
        "volume",
        "sma_7",
        "sma_14", 
        "sma_21",
        "sma_60",
        "ema_7",
        "ema_14",
        "ema_21", 
        "ema_60",
        "rsi_7",
        "rsi_14",
        "rsi_21",
        "rsi_60",
        "macd_7",
        "macdsignal_7",
        "macdhist_7",
        "obv"
    ]

    @field_validator("app_name")
    @classmethod
    def validate_app_name_field(cls, v: str) -> str:
        if not v or len(v) > 100:
            raise ValueError("app_name must be 1-100 characters")
        if not re.match(r'^[a-zA-Z0-9\-\_]+$', v):
            raise ValueError("app_name can only contain alphanumeric, hyphens, underscores")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level_field(cls, v: str) -> str:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of: {', '.join(valid_levels)}")
        return v.upper()

    @field_validator("kafka_broker_address")
    @classmethod
    def validate_kafka_broker_field(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9\-\.]+:\d+$', v):
            raise ValueError("kafka_broker_address must be in format 'host:port'")
        port = int(v.split(':')[-1])
        if not 1 <= port <= 65535:
            raise ValueError("port must be between 1 and 65535")
        return v

    @field_validator("kafka_input_topic", "kafka_output_topic")
    @classmethod
    def validate_topic_name_field(cls, v: str) -> str:
        if not v or len(v) > 255 or v.startswith(('.', '_')):
            raise ValueError("topic name must be 1-255 chars, cannot start with . or _")
        if not re.match(r'^[a-zA-Z0-9\-\_\.]+$', v):
            raise ValueError("topic name can only contain alphanumeric, hyphens, underscores, dots")
        return v

    @field_validator("kafka_consumer_group")
    @classmethod
    def validate_consumer_group_field(cls, v: str) -> str:
        if not v or len(v) > 255:
            raise ValueError("consumer group must be 1-255 characters")
        if not re.match(r'^[a-zA-Z0-9\-\_]+$', v):
            raise ValueError("consumer group can only contain alphanumeric, hyphens, underscores")
        return v

    @field_validator("candle_seconds")
    @classmethod
    def validate_candle_interval_field(cls, v: int) -> int:
        if not 1 <= v <= 86400:
            raise ValueError("candle_seconds must be between 1 and 86400 (1 day)")
        return v

    @field_validator("processing_mode")
    @classmethod
    def validate_processing_mode_field(cls, v: str) -> str:
        if v not in ["live", "historical"]:
            raise ValueError("processing_mode must be either 'live' or 'historical'")
        return v

    @field_validator("prediction_horizon_seconds")
    @classmethod
    def validate_prediction_horizon_field(cls, v: int) -> int:
        if not 1 <= v <= 86400:
            raise ValueError("prediction_horizon_seconds must be between 1 and 86400 (1 day)")
        return v

    @field_validator("pair")
    @classmethod
    def validate_pair_field(cls, v: str) -> str:
        pattern = r'^[A-Z0-9]{2,10}[\/\-]?[A-Z0-9]{2,10}$'
        if not re.match(pattern, v.upper()):
            raise ValueError(f"'{v}' invalid trading pair format")
        return v.upper()

    @field_validator("risingwave_port")
    @classmethod
    def validate_port_field(cls, v: int) -> int:
        if not 1 <= v <= 65535:
            raise ValueError("port must be between 1 and 65535")
        return v

    @field_validator("train_test_split_ratio")
    @classmethod
    def validate_split_ratio_field(cls, v: float) -> float:
        if not 0.1 <= v <= 0.9:
            raise ValueError("train_test_split_ratio must be between 0.1 and 0.9")
        return v

    @field_validator("max_percentage_rows_with_missing_values")
    @classmethod
    def validate_missing_values_field(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("max_percentage_rows_with_missing_values must be between 0.0 and 1.0")
        return v

    @field_validator("hyperparam_search_trials")
    @classmethod
    def validate_trials_field(cls, v: int) -> int:
        if v < 0:
            raise ValueError("hyperparam_search_trials must be non-negative")
        return v

    @model_validator(mode="after")
    def validate_constraints(self) -> "Settings":
        # Validate log format
        if self.log_format not in ["json", "text"]:
            raise ValueError("log_format must be either 'json' or 'text'")

        # Business rule: production environments should use WARNING or higher log level
        if "prod" in self.app_name.lower() and self.log_level in ["DEBUG", "INFO"]:
            logger.warning(
                f"Production app '{self.app_name}' using log level '{self.log_level}'. "
                "Consider using WARNING or ERROR for production."
            )

        # Validate training data horizon is positive
        if self.training_data_horizon_days <= 0:
            raise ValueError("training_data_horizon_days must be positive")

        return self


def load_settings() -> Settings:
    return Settings()