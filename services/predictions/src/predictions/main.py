#!/usr/bin/env python3

from typing import Dict, Any
import json

from loguru import logger
from quixstreams import Application

from predictions.config import load_settings, Settings
from predictions.models import Prediction, PredictionError


def dummy_model_prediction(indicators: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder model prediction function.
    In real implementation, this would load an ML model and make predictions.
    """
    # Simple dummy prediction based on RSI
    rsi_14 = indicators.get('rsi_14', 50.0)
    
    # Simple logic: if RSI < 30, predict price up; if RSI > 70, predict price down
    if rsi_14 < 30:
        prediction_value = float(indicators.get('close', 100)) * 1.02  # 2% increase
        confidence = 0.7
        signal_strength = 0.5
    elif rsi_14 > 70:
        prediction_value = float(indicators.get('close', 100)) * 0.98  # 2% decrease
        confidence = 0.7
        signal_strength = -0.5
    else:
        prediction_value = float(indicators.get('close', 100))  # No change
        confidence = 0.5
        signal_strength = 0.0
    
    return {
        'prediction_value': prediction_value,
        'confidence_score': confidence,
        'model_name': 'dummy_rsi_model',
        'model_version': '1.0.0',
        'prediction_horizon_minutes': 5,
        'features_used': ['rsi_14', 'close'],
        'signal_strength': signal_strength,
        'prediction_type': 'price_direction'
    }


def validate_indicators_optional(indicators: dict) -> None:
    """Optional indicators validation - logs warnings but doesn't stop processing."""
    try:
        # Basic validation
        required_fields = ['pair', 'close', 'window_start_ms', 'window_end_ms']
        for field in required_fields:
            if field not in indicators:
                logger.warning(f"Missing required field in indicators: {field}")
                return
        
        logger.debug(f"Validated indicators: {indicators['pair']}")
    except Exception as e:
        logger.warning(f"Indicators validation warning: {e}")


def process_indicators_to_prediction(indicators: dict, settings: Settings) -> dict:
    """Process technical indicators and generate prediction."""
    try:
        # Run model prediction
        model_output = dummy_model_prediction(indicators)
        
        # Create prediction object
        prediction = Prediction.from_indicators(indicators, model_output)
        
        return prediction.to_dict()
        
    except PredictionError as e:
        logger.error(f"Prediction generation failed: {e.message}")
        # Return empty prediction for graceful degradation
        return {}
    except Exception as e:
        logger.error(f"Unexpected error in prediction processing: {e}")
        return {}


def run_predictions_service(settings: Settings) -> None:
    """Main predictions processing service."""
    logger.info(f"Starting predictions service in {settings.processing_mode} mode...")

    # Configure application based on processing mode
    app_config = {
        "broker_address": settings.kafka_broker_address,
        "consumer_group": settings.kafka_consumer_group,
    }
    
    # For historical processing, read from beginning of topic
    if settings.processing_mode == "historical":
        app_config["auto_offset_reset"] = "earliest"
        logger.info("Historical mode: will process from beginning of topic")
    
    app = Application(**app_config)

    # Input and output topics
    indicators_topic = app.topic(
        settings.kafka_input_topic,
        value_deserializer='json',
    )

    predictions_topic = app.topic(
        settings.kafka_output_topic,
        value_serializer='json',
    )

    # Create streaming dataframe
    sdf = app.dataframe(topic=indicators_topic)

    # Optional validation (non-blocking)
    sdf = sdf.update(validate_indicators_optional)

    # Filter by candle_seconds if specified
    if hasattr(settings, 'candle_seconds') and settings.candle_seconds:
        sdf = sdf[sdf['candle_seconds'] == settings.candle_seconds]

    # Process indicators to generate predictions
    sdf = sdf.apply(lambda indicators: process_indicators_to_prediction(indicators, settings))

    # Filter out empty predictions
    sdf = sdf[sdf.apply(lambda x: len(x) > 0)]

    # Log predictions for debugging
    sdf = sdf.update(lambda value: logger.debug(f'Prediction: {value}'))

    # Send to output topic
    sdf = sdf.to_topic(predictions_topic)

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
        logger.info(f"Prediction horizon: {settings.prediction_horizon_seconds} seconds")
        logger.success("Configuration loaded successfully!")

        run_predictions_service(settings)

    except KeyboardInterrupt:
        logger.info("Shutting down predictions service...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        exit(1)


if __name__ == "__main__":
    main()