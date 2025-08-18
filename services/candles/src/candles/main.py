#!/usr/bin/env python3

from loguru import logger
from config.config import settings

if __name__ == "__main__":
    logger.info(f"App name: {settings.app_name}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Kafka broker: {settings.kafka_broker_address}")
    logger.info(f"Input topic: {settings.kafka_input_topic}")
    logger.info(f"Output topic: {settings.kafka_output_topic}")
    logger.info(f"Candle interval: {settings.candle_seconds} seconds")
    logger.success("Settings imported successfully!")