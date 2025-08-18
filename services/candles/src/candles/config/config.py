import os
from pydantic import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=f'.env.{os.getenv("ENV", "development")}',
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
