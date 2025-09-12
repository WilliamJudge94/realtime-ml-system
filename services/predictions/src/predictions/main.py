"""Main predictions service for real-time streaming."""

from loguru import logger

from predictions.config import load_settings
from predictions.utils.streaming import (
    create_streaming_application,
    setup_streaming_dataflow,
)
from predictions.utils.constants import ERROR_EXIT_CODE


def run_predictions_service(settings) -> None:
    """
    Main predictions processing service using streaming utilities.
    
    Args:
        settings: Application settings configuration
    """
    logger.info(
        f"Starting predictions service in {settings.processing_mode} mode...")

    # Create and configure streaming application
    app = create_streaming_application(settings)
    
    # Set up the streaming dataflow
    setup_streaming_dataflow(app, settings)

    logger.success("Predictions service started successfully!")
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
        logger.info(f"Model: {settings.model_name} v{settings.model_version}")
        logger.info(
            f"Prediction horizon: {settings.prediction_horizon_seconds} seconds")
        logger.success("Configuration loaded successfully!")

        run_predictions_service(settings)

    except KeyboardInterrupt:
        logger.info("Shutting down predictions service...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        exit(ERROR_EXIT_CODE)


if __name__ == "__main__":
    main()