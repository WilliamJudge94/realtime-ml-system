# Candles Service

A real-time OHLCV (Open, High, Low, Close, Volume) candle aggregation service that processes cryptocurrency trade streams and produces candlestick data using tumbling window aggregation.

## Features

- **Real-time Aggregation**: Transforms individual trade events into OHLCV candles using tumbling windows
- **Configurable Intervals**: Supports configurable candle time intervals (default: 60 seconds)
- **Data Validation**: Built-in validation for both input trades and output candles using Pydantic models
- **Graceful Error Handling**: Non-blocking validation with warning logs for malformed data
- **Kafka Integration**: Consumes from trade topics and produces to candle topics with JSON serialization
- **Custom Timestamp Extraction**: Uses trade timestamp instead of Kafka message timestamp for accurate windowing
- **Intermediate Results**: Emits intermediate candle updates for real-time monitoring

## Architecture

The service processes data in the following pipeline:
1. **Ingestion**: Consumes trade messages from Kafka input topic
2. **Validation**: Optional trade validation (logs warnings but continues processing)
3. **Windowing**: Groups trades into tumbling windows based on configurable time intervals
4. **Aggregation**: Reduces trades into OHLCV format using custom reducer functions
5. **Validation**: Validates final candle data structure and format
6. **Output**: Publishes validated candles to Kafka output topic

## Dependencies

- **quixstreams**: Kafka streaming library for real-time data processing
- **pydantic**: Data validation and serialization framework
- **loguru**: Structured logging with debug capabilities
- **Python 3.13+**: Modern Python runtime

## Data Models

### Input Trade Format
```json
{
  "product_id": "XBT/USD",
  "price": "45000.50",
  "quantity": "0.1234",
  "timestamp_ms": 1640995200000
}
```

### Output Candle Format
```json
{
  "pair": "XBT/USD",
  "open": 45000.50,
  "high": 45100.00,
  "low": 44950.25,
  "close": 45075.30,
  "volume": 1.2345,
  "window_start_ms": 1640995200000,
  "window_end_ms": 1640995260000,
  "candle_seconds": 60
}
```

## Configuration

The service is configured through environment variables managed by the config module:

- `KAFKA_BROKER_ADDRESS`: Kafka broker connection string
- `KAFKA_INPUT_TOPIC`: Input topic for trade messages
- `KAFKA_OUTPUT_TOPIC`: Output topic for candle messages  
- `KAFKA_CONSUMER_GROUP`: Consumer group for the service
- `CANDLE_SECONDS`: Time interval for candle aggregation (default: 60)
- `LOG_LEVEL`: Logging verbosity level
- `DEBUG`: Enable debug mode for detailed logging

## Usage

```bash
# Install dependencies
uv pip install -e .

# Run the service
python -m candles.main
```

## Monitoring and Debugging

The service provides comprehensive logging at different levels:
- **INFO**: Service startup, configuration, and status messages
- **DEBUG**: Individual trade and candle processing details
- **WARNING**: Non-fatal validation issues with input data
- **ERROR**: Critical validation failures and processing errors

Enable debug logging by setting `DEBUG=true` and `LOG_LEVEL=DEBUG` in your environment.

## Development Setup

For development environment setup, Kubernetes cluster configuration, and project overview, see the main [project README](../../README.md).

## Integration

This service is part of the real-time ML trading system pipeline:
- **Upstream**: Receives trade data from the [Trades Service](../trades/README.md)
- **Downstream**: Feeds candle data to the [Technical Indicators Service](../technical_indicators/README.md)