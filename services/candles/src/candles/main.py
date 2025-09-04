#!/usr/bin/env python3

from typing import Any, List, Optional, Tuple
from datetime import timedelta

from loguru import logger
from quixstreams import Application
from quixstreams.models import TimestampType

from config.config import load_settings
from models import Trade, Candle, CandleError


def custom_ts_extractor(
    value: Any,
    headers: Optional[List[Tuple[str, bytes]]],
    timestamp: float,
    timestamp_type: TimestampType,
) -> int:
    """Extract timestamp from message payload instead of Kafka timestamp."""
    return value['timestamp_ms']


def init_candle(trade: dict) -> dict:
    """Initialize a candle with the first trade."""
    return {
        'open': float(trade['price']),
        'high': float(trade['price']),
        'low': float(trade['price']),
        'close': float(trade['price']),
        'volume': float(trade['quantity']),
        'pair': trade['product_id'],
    }


def update_candle(candle: dict, trade: dict) -> dict:
    """Update candle state with new trade."""
    price = float(trade['price'])
    quantity = float(trade['quantity'])

    candle['high'] = max(candle['high'], price)
    candle['low'] = min(candle['low'], price)
    candle['close'] = price
    candle['volume'] += quantity

    return candle


def validate_and_format_candle(candle_data: dict) -> dict:
    """Validate and format candle for output."""
    try:
        # Create Candle for validation
        candle = Candle.from_aggregation(
            candle_data={
                'open': candle_data['open'],
                'high': candle_data['high'],
                'low': candle_data['low'],
                'close': candle_data['close'],
                'volume': candle_data['volume'],
                'pair': candle_data['pair'],
            },
            window_info={
                'window_start_ms': candle_data['window_start_ms'],
                'window_end_ms': candle_data['window_end_ms'],
                'candle_seconds': candle_data.get('candle_seconds', 60)
            }
        )

        return candle.to_dict()

    except CandleError as e:
        logger.error(f"Candle validation failed: {e.message}")
        # Return original data if validation fails for graceful degradation
        return candle_data


def validate_trade_optional(trade: dict) -> None:
    """Optional trade validation - logs warnings but doesn't stop processing."""
    try:
        Trade.from_dict(trade)
        logger.debug(f"Validated trade: {trade['product_id']}")
    except CandleError as e:
        logger.warning(f"Trade validation warning: {e.message}")


def run_candles_service(settings):
    """Main candles processing service."""
    logger.info(f"Starting candles service in {settings.processing_mode} mode...")

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
    trades_topic = app.topic(
        settings.kafka_input_topic,
        value_deserializer='json',
        timestamp_extractor=custom_ts_extractor,
    )

    candles_topic = app.topic(
        settings.kafka_output_topic,
        value_serializer='json',
    )

    # Create streaming dataframe
    sdf = app.dataframe(topic=trades_topic)

    # Optional validation (non-blocking)
    sdf = sdf.update(validate_trade_optional)

    # Aggregate trades into candles
    sdf = (
        sdf.tumbling_window(timedelta(seconds=settings.candle_seconds))
        .reduce(reducer=update_candle, initializer=init_candle)
        .current()  # Emit intermediate results
    )

    # Extract OHLCV fields and add metadata
    sdf['open'] = sdf['value']['open']
    sdf['high'] = sdf['value']['high']
    sdf['low'] = sdf['value']['low']
    sdf['close'] = sdf['value']['close']
    sdf['volume'] = sdf['value']['volume']
    sdf['pair'] = sdf['value']['pair']
    sdf['window_start_ms'] = sdf['start']
    sdf['window_end_ms'] = sdf['end']
    sdf['candle_seconds'] = settings.candle_seconds

    # Select relevant columns
    sdf = sdf[
        [
            'pair', 'open', 'high', 'low', 'close', 'volume',
            'window_start_ms', 'window_end_ms', 'candle_seconds',
        ]
    ]

    # Validate and format output
    sdf = sdf.update(validate_and_format_candle)

    # Log candles for debugging
    sdf = sdf.update(lambda value: logger.debug(f'Candle: {value}'))

    # Send to output topic
    sdf = sdf.to_topic(candles_topic)

    logger.success("Candles service started successfully!")
    app.run()


if __name__ == "__main__":
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
        logger.success("Configuration loaded successfully!")

        run_candles_service(settings)

    except KeyboardInterrupt:
        logger.info("Shutting down candles service...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        exit(1)
