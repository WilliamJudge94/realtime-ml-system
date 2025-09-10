import re
from loguru import logger
from pathlib import Path
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

    # Prediction processing settings
    candle_seconds: int = 60
    processing_mode: str = "live"
    
    # Model settings
    model_name: str = "default_model"
    model_version: str = "latest"
    prediction_horizon_minutes: int = 5

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

    @field_validator("prediction_horizon_minutes")
    @classmethod
    def validate_prediction_horizon_field(cls, v: int) -> int:
        if not 1 <= v <= 1440:
            raise ValueError("prediction_horizon_minutes must be between 1 and 1440 (1 day)")
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

        return self


def load_settings() -> Settings:
    return Settings()