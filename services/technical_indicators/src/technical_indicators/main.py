#!/usr/bin/env python3

from loguru import logger
from quixstreams import Application

from config.config import load_settings, Settings
from candle import update_candles_in_state
from indicators import compute_technical_indicators
from table import create_table_in_risingwave, test_risingwave_connectivity


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
        auto_offset_reset="earliest",
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
        logger.info(f"RisingWave configuration:")
        logger.info(f"  Host: {settings.risingwave_host}")
        logger.info(f"  Port: {settings.risingwave_port}")
        logger.info(f"  User: {settings.risingwave_user}")
        logger.info(f"  Database: {settings.risingwave_database}")
        logger.info(f"  Table name: {settings.table_name_in_risingwave}")
        logger.info(f"  Password configured: {'Yes' if settings.risingwave_password else 'No'}")
        logger.info(f"  Full connection string: postgresql://{settings.risingwave_user}@{settings.risingwave_host}:{settings.risingwave_port}/{settings.risingwave_database}")
        logger.success("Configuration loaded successfully!")

        # Initialize RisingWave table before starting the service
        logger.info("=== RISINGWAVE TABLE INITIALIZATION ===")
        logger.info("Preparing to initialize RisingWave table with the following parameters:")
        logger.info(f"  Table name: {settings.table_name_in_risingwave}")
        logger.info(f"  Kafka broker: {settings.kafka_broker_address}")
        logger.info(f"  Kafka topic: {settings.kafka_output_topic}")
        logger.info(f"  RisingWave endpoint: {settings.risingwave_host}:{settings.risingwave_port}")
        logger.info(f"  RisingWave database: {settings.risingwave_database}")
        logger.info(f"  RisingWave user: {settings.risingwave_user}")
        
        # First test connectivity
        logger.info("Testing RisingWave connectivity before table creation...")
        connectivity_ok = test_risingwave_connectivity(
            risingwave_host=settings.risingwave_host,
            risingwave_port=settings.risingwave_port,
            risingwave_user=settings.risingwave_user,
            risingwave_password=settings.risingwave_password,
            risingwave_database=settings.risingwave_database,
        )
        
        if not connectivity_ok:
            logger.error("RisingWave connectivity test failed - aborting table creation")
            logger.warning("Service will continue but RisingWave integration will not work")
            table_created = False
        else:
            logger.info("Starting RisingWave table creation process...")
            table_created = create_table_in_risingwave(
                table_name=settings.table_name_in_risingwave,
                kafka_broker_address=settings.kafka_broker_address,
                kafka_topic=settings.kafka_output_topic,
                risingwave_host=settings.risingwave_host,
                risingwave_port=settings.risingwave_port,
                risingwave_user=settings.risingwave_user,
                risingwave_password=settings.risingwave_password,
                risingwave_database=settings.risingwave_database,
            )
        
        if table_created:
            logger.success("=== RISINGWAVE INITIALIZATION SUCCESS ===")
            logger.success(f"Table '{settings.table_name_in_risingwave}' is ready for data ingestion")
            logger.success(f"RisingWave will automatically consume from Kafka topic '{settings.kafka_output_topic}'")
            logger.success(f"Data will be available for real-time queries at: {settings.risingwave_host}:{settings.risingwave_port}")
        else:
            logger.error("=== RISINGWAVE INITIALIZATION FAILED ===")
            logger.warning("RisingWave table initialization failed, but continuing with service startup")
            logger.warning("This means technical indicators will be produced to Kafka but not ingested into RisingWave")
            logger.warning("Check RisingWave connectivity and configuration")

        run_technical_indicators_service(settings)

    except KeyboardInterrupt:
        logger.info("=== SHUTDOWN INITIATED ===")
        logger.info("Shutting down technical indicators service...")
        logger.info("RisingWave connections will be closed gracefully")
    except Exception as e:
        logger.error("=== CRITICAL ERROR ===")
        logger.error(f"Unexpected error in technical indicators service: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        logger.error("This may affect RisingWave data ingestion")
        raise


if __name__ == "__main__":
    main()
