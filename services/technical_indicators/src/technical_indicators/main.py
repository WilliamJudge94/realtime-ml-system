#!/usr/bin/env python3

from loguru import logger
from quixstreams import Application

from config.config import load_settings, Settings
from candle import update_candles_in_state
from indicators import compute_technical_indicators


def run_technical_indicators_service(settings: Settings) -> None:
    """
    Transforms a stream of input candles into a stream of technical indicators.

    In 5 steps:
    - Ingests candles from the input Kafka topic
    - Filters candles by the given candle_seconds
    - Adds candles to the state dictionary  
    - Computes technical indicators from the candles in the state
    - Produces technical indicators to the output Kafka topic

    Args:
        settings: Configuration settings object

    Returns:
        None
    """
    logger.info("Starting technical indicators service...")

    app = Application(
        broker_address=settings.kafka_broker_address,
        consumer_group=settings.kafka_consumer_group,
    )

    # Input and output topics
    candles_topic = app.topic(
        settings.kafka_input_topic, value_deserializer='json')
    technical_indicators_topic = app.topic(
        settings.kafka_output_topic, value_serializer='json')

    # Step 1. Ingest candles from the input kafka topic
    # Create a Streaming DataFrame connected to the input Kafka topic
    sdf = app.dataframe(topic=candles_topic)

    # Step 2. Filter the candles by the given `candle_seconds`
    sdf = sdf[sdf['candle_seconds'] == settings.candle_seconds]

    # Step 3. Add candles to the state dictionary
    sdf = sdf.apply(lambda candle, state: update_candles_in_state(
        candle, state, settings), stateful=True)

    # Step 4. Compute technical indicators from the candles in the state dictionary
    sdf = sdf.apply(lambda candle, state: compute_technical_indicators(
        candle, state, settings), stateful=True)

    # Log technical indicators for debugging
    sdf = sdf.update(lambda value: logger.debug(
        f'Technical indicator: {value}'))

    # Step 5. Produce the technical indicators to the output kafka topic
    sdf = sdf.to_topic(technical_indicators_topic)

    logger.info("Technical indicators service started successfully!")
    # Starts the streaming app
    app.run()


def main() -> None:
    """Main entry point with proper error handling and logging."""
    try:
        settings = load_settings()

        logger.info(f"App name: {settings.app_name}")
        logger.info(f"Debug mode: {settings.debug}")
        logger.info(f"Log level: {settings.log_level}")
        logger.info(f"Kafka broker: {settings.kafka_broker_address}")
        logger.info(f"Input topic: {settings.kafka_input_topic}")
        logger.info(f"Output topic: {settings.kafka_output_topic}")
        logger.info(f"Consumer group: {settings.kafka_consumer_group}")
        logger.info(f"Candle interval: {settings.candle_seconds} seconds")
        logger.info(f"Max candles in state: {settings.max_candles_in_state}")
        logger.success("Configuration loaded successfully!")

        run_technical_indicators_service(settings)

    except KeyboardInterrupt:
        logger.info("Shutting down technical indicators service...")
    except Exception as e:
        logger.error(f"Unexpected error in technical indicators service: {e}")
        raise


if __name__ == "__main__":
    main()
