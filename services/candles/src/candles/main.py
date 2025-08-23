#!/usr/bin/env python3

from typing import Any, List, Optional, Tuple

from loguru import logger
from quixstreams import Application
from quixstreams.models import TimestampType

from config.config import load_settings
from models import TradeMessage, CandleOutput, InvalidTradeError, ValidationError


def custom_ts_extractor(
    value: Any,
    headers: Optional[List[Tuple[str, bytes]]],
    timestamp: float,
    timestamp_type: TimestampType,
) -> int:
    """
    Extract timestamp from message payload instead of Kafka timestamp.
    """
    return value['timestamp_ms']


def init_candle(trade: dict) -> dict:
    """
    Initialize a candle with the first trade.
    Enhanced with optional validation.
    """
    try:
        # Optional: validate incoming trade data
        validated_trade = TradeMessage.from_dict(trade)
        logger.debug(f"Validated trade: {validated_trade.product_id}")
    except InvalidTradeError as e:
        logger.warning(f"Invalid trade data: {e.message}")
        # Continue processing with original data for now
    
    return {
        'open': float(trade['price']),
        'high': float(trade['price']),
        'low': float(trade['price']),
        'close': float(trade['price']),
        'volume': float(trade['quantity']),
        'pair': trade['product_id'],
    }


def update_candle(candle: dict, trade: dict) -> dict:
    """
    Update candle state with new trade.
    Enhanced with optional validation.
    """
    try:
        # Optional: validate incoming trade data
        validated_trade = TradeMessage.from_dict(trade)
    except InvalidTradeError as e:
        logger.warning(f"Invalid trade data: {e.message}")
        # Continue processing with original data for now
    
    # Update OHLCV
    candle['high'] = max(candle['high'], float(trade['price']))
    candle['low'] = min(candle['low'], float(trade['price']))
    candle['close'] = float(trade['price'])
    candle['volume'] += float(trade['quantity'])
    
    return candle


def validate_and_format_candle(candle_data: dict) -> dict:
    """
    Validate and format candle output using our new model.
    """
    try:
        # Create CandleOutput for validation - the structure is now flat
        candle_output = CandleOutput.from_aggregation_result(
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
        
        # Return validated data as dict for Kafka
        return candle_output.to_kafka_message()
        
    except ValidationError as e:
        logger.error(f"Candle validation failed: {e.message}")
        # Return original data if validation fails
        return candle_data


def run_candles_service(settings):
    """
    Main candles processing service with enhanced validation.
    """
    logger.info("Starting candles service...")
    
    app = Application(
        broker_address=settings.kafka_broker_address,
        consumer_group=settings.kafka_consumer_group,
    )

    # Input topic
    trades_topic = app.topic(
        settings.kafka_input_topic,
        value_deserializer='json',
        timestamp_extractor=custom_ts_extractor,
    )
    
    # Output topic
    candles_topic = app.topic(
        settings.kafka_output_topic,
        value_serializer='json',
    )

    # Create streaming dataframe
    sdf = app.dataframe(topic=trades_topic)

    # Aggregate trades into candles using tumbling windows
    from datetime import timedelta
    
    sdf = (
        sdf.tumbling_window(timedelta(seconds=settings.candle_seconds))
        .reduce(reducer=update_candle, initializer=init_candle)
    )

    # Emit intermediate candles for responsiveness
    sdf = sdf.current()

    # Extract OHLCV fields
    sdf['open'] = sdf['value']['open']
    sdf['high'] = sdf['value']['high'] 
    sdf['low'] = sdf['value']['low']
    sdf['close'] = sdf['value']['close']
    sdf['volume'] = sdf['value']['volume']
    sdf['pair'] = sdf['value']['pair']

    # Add window timestamps
    sdf['window_start_ms'] = sdf['start']
    sdf['window_end_ms'] = sdf['end']
    sdf['candle_seconds'] = settings.candle_seconds

    # Select relevant columns
    sdf = sdf[
        [
            'pair',
            'open',
            'high', 
            'low',
            'close',
            'volume',
            'window_start_ms',
            'window_end_ms',
            'candle_seconds',
        ]
    ]

    # Apply validation and formatting
    sdf = sdf.update(validate_and_format_candle)

    # Log candles
    sdf = sdf.update(lambda value: logger.debug(f'Candle: {value}'))

    # Produce to output topic
    sdf = sdf.to_topic(candles_topic)

    logger.success("Candles service started successfully!")
    
    # Start the streaming application
    app.run()


if __name__ == "__main__":
    try:
        # Load configuration
        settings = load_settings()
        
        logger.info(f"App name: {settings.app_name}")
        logger.info(f"Debug mode: {settings.debug}")
        logger.info(f"Log level: {settings.log_level}")
        logger.info(f"Kafka broker: {settings.kafka_broker_address}")
        logger.info(f"Input topic: {settings.kafka_input_topic}")
        logger.info(f"Output topic: {settings.kafka_output_topic}")
        logger.info(f"Candle interval: {settings.candle_seconds} seconds")
        logger.success("Configuration loaded successfully!")
        
        # Run the candles service
        run_candles_service(settings)
        
    except KeyboardInterrupt:
        logger.info("Shutting down candles service...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        exit(1)