import os
from loguru import logger
from pathlib import Path
from typing import List
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from .validators import (
    validate_candle_interval,
    validate_kafka_broker,
    validate_log_level,
    validate_topic_name,
    validate_consumer_group,
    validate_app_name,
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent / "local.env",
        env_prefix="CANDLES_",
        case_sensitive=False,
    )

    logger.debug(f"Loading settings from {Path(__file__).parent / 'local.env'}")

    # Application settings
    app_name: str = "candles"
    debug: bool = False
    log_level: str = "INFO"
    log_format: str = "json"

    # Kafka settings
    kafka_broker_address: str = "localhost:9092"
    kafka_input_topic: str = "trades"
    kafka_output_topic: str = "candles"
    kafka_consumer_group: str = "candles_consumer_group"

    # Candle processing settings
    candle_seconds: int = 60

    @field_validator("app_name")
    @classmethod
    def validate_app_name_field(cls, v: str) -> str:
        return validate_app_name(cls, v)

    @field_validator("log_level")
    @classmethod
    def validate_log_level_field(cls, v: str) -> str:
        return validate_log_level(cls, v)

    @field_validator("kafka_broker_address")
    @classmethod
    def validate_kafka_broker_field(cls, v: str) -> str:
        return validate_kafka_broker(cls, v)

    @field_validator("kafka_input_topic", "kafka_output_topic")
    @classmethod
    def validate_topic_name_field(cls, v: str) -> str:
        return validate_topic_name(cls, v)

    @field_validator("kafka_consumer_group")
    @classmethod
    def validate_consumer_group_field(cls, v: str) -> str:
        return validate_consumer_group(cls, v)

    @field_validator("candle_seconds")
    @classmethod
    def validate_candle_interval_field(cls, v: int) -> int:
        return validate_candle_interval(cls, v)

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