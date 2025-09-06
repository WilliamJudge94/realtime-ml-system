import re
from typing import Union
from loguru import logger
from pathlib import Path
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent / "local.env",
        env_prefix="TECHNICAL_INDICATORS_",
        case_sensitive=False,
    )

    logger.debug(f"Loading settings from {Path(__file__).parent / 'local.env'}")

    # Application settings
    app_name: str = "technical_indicators"
    debug: bool = False
    log_level: str = "INFO"
    log_format: str = "json"

    # Kafka settings
    kafka_broker_address: str = "localhost:9092"
    kafka_input_topic: str = "candles"
    kafka_output_topic: str = "technical_indicators"
    kafka_consumer_group: str = "technical_indicators_consumer_group"

    # Technical Indicators specific settings
    candle_seconds: int = 60
    max_candles_in_state: int = 70
    table_name_in_risingwave: str = "technical_indicators"
    processing_mode: str = "live"
    
    # RisingWave connection settings
    risingwave_host: str = "localhost"
    risingwave_port: int = 4567
    risingwave_user: str = "root"
    risingwave_password: str = ""
    risingwave_database: str = "dev"
    
    # Indicator periods configuration
    sma_periods: Union[str, list[int]] = [7, 14, 21, 60]
    ema_periods: Union[str, list[int]] = [7, 14, 21, 60]
    rsi_periods: Union[str, list[int]] = [7, 14, 21, 60]

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

    @field_validator("max_candles_in_state")
    @classmethod
    def validate_max_candles_field(cls, v: int) -> int:
        if not 1 <= v <= 10000:
            raise ValueError("max_candles_in_state must be between 1 and 10000")
        return v

    @field_validator("table_name_in_risingwave")
    @classmethod
    def validate_table_name_field(cls, v: str) -> str:
        if not v or len(v) > 63:
            raise ValueError("table name must be 1-63 characters")
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9\_]*$', v):
            raise ValueError("table name must start with letter and contain only alphanumeric and underscores")
        return v

    @field_validator("risingwave_host")
    @classmethod
    def validate_risingwave_host_field(cls, v: str) -> str:
        if not v or len(v) > 255:
            raise ValueError("risingwave_host must be 1-255 characters")
        return v

    @field_validator("risingwave_port")
    @classmethod
    def validate_risingwave_port_field(cls, v: int) -> int:
        if not 1 <= v <= 65535:
            raise ValueError("risingwave_port must be between 1 and 65535")
        return v

    @field_validator("risingwave_user")
    @classmethod
    def validate_risingwave_user_field(cls, v: str) -> str:
        if not v or len(v) > 63:
            raise ValueError("risingwave_user must be 1-63 characters")
        return v

    @field_validator("risingwave_database")
    @classmethod
    def validate_risingwave_database_field(cls, v: str) -> str:
        if not v or len(v) > 63:
            raise ValueError("risingwave_database must be 1-63 characters")
        return v

    @field_validator("processing_mode")
    @classmethod
    def validate_processing_mode_field(cls, v: str) -> str:
        if v not in ["live", "historical"]:
            raise ValueError("processing_mode must be either 'live' or 'historical'")
        return v

    @field_validator("sma_periods", "ema_periods", "rsi_periods", mode="before")
    @classmethod
    def validate_periods_field(cls, v) -> list[int]:
        # Handle comma-separated string from environment variables
        if isinstance(v, str):
            try:
                v = [int(period.strip()) for period in v.split(',') if period.strip()]
            except ValueError:
                raise ValueError("periods must be comma-separated integers")
        
        if not v:
            raise ValueError("periods list cannot be empty")
        for period in v:
            if not isinstance(period, int) or period < 1:
                raise ValueError("all periods must be positive integers")
        return sorted(list(set(v)))  # Remove duplicates and sort

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
