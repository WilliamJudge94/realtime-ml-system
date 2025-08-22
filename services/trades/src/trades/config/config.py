import os
from loguru import logger
from pathlib import Path
from typing import List
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from .validators import validate_live_or_historical, validate_product_ids


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent / "local.env",
        env_prefix="TRADES_",
        case_sensitive=False,
    )

    logger.debug(f"Loading settings from {Path(__file__).parent / 'local.env'}")

    # Application settings
    app_name: str = "trades"
    debug: bool = False
    log_level: str = "INFO"
    log_format: str = "json"

    # Kafka settings
    kafka_broker_address: str = "localhost:9092"
    kafka_topic_name: str = "trades"

    # Trading settings
    live_or_historical: str = "live"
    product_ids: List[str] = ["BTC/USD"]
    last_n_days: int = 1

    @field_validator("live_or_historical")
    @classmethod
    def validate_live_or_historical_field(cls, v: str) -> str:
        return validate_live_or_historical(cls, v)

    @field_validator("product_ids")
    @classmethod
    def validate_product_ids_field(cls, v: List[str]) -> List[str]:
        return validate_product_ids(cls, v)

    @model_validator(mode="after")
    def validate_constraints(self) -> "Settings":
        if self.live_or_historical == "historical" and self.last_n_days <= 0:
            raise ValueError(
                "last_n_days must be positive for historical mode"
            )
        return self


def load_settings() -> Settings:
    return Settings()
