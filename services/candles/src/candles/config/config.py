import os
from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    _config_dir = os.path.dirname(os.path.abspath(__file__))
    _env = os.getenv('ENV')
    if _env is None:
        logger.warning("ENV environment variable not set, using default 'development' configuration")
        _env = 'development'
    _settings_file = os.path.join(_config_dir, f".env.{_env}")
    logger.debug(f"Loading settings from {_settings_file}")
    model_config = SettingsConfigDict(
        env_file=_settings_file,
        env_file_encoding="utf-8",
        env_prefix="CANDLES_",
        case_sensitive=False,
        extra="forbid",
    )

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


settings = Settings()
