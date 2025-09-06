# Candles Service

A real-time OHLCV (Open, High, Low, Close, Volume) candle aggregation service that processes cryptocurrency trade streams and produces candlestick data using tumbling window aggregation. The service supports both live and historical processing modes with robust data validation and error handling.

## Architecture

The candles service implements a sophisticated stream processing pipeline with multiple validation layers:

### Processing Pipeline
1. **Ingestion**: Consumes trade messages from Kafka input topic
2. **Timestamp Extraction**: Uses trade timestamp (not Kafka timestamp) for accurate windowing
3. **Optional Validation**: Non-blocking trade validation with warning logs
4. **Windowing**: Groups trades into tumbling windows based on configurable intervals
5. **Aggregation**: Reduces trades into OHLCV format using stateful reducers
6. **Validation**: Validates final candle data structure and OHLC relationships
7. **Output**: Publishes validated candles to Kafka output topic

### Processing Modes

#### Live Mode (Default)
- Processes trade data in real-time as it arrives
- Uses Kafka consumer group with latest offset
- Continuously aggregates trades into rolling candle windows
- Emits intermediate results for real-time monitoring

#### Historical Mode
- Processes historical trade data from beginning of topic
- Sets `auto_offset_reset=earliest` for complete data processing
- Sequentially processes all available trades
- Maintains the same windowing logic for consistent results

### Tumbling Window Mechanism
The service uses QuixStreams tumbling windows with custom timestamp extraction:
- **Window Size**: Configurable interval (default: 60 seconds)
- **Timestamp Source**: Trade `timestamp_ms` field (not Kafka message timestamp)
- **Intermediate Results**: Emits candle updates as trades arrive within windows
- **State Management**: Maintains running OHLCV state with reducer functions

## Data Models

### Trade Model
Input trade validation with comprehensive field validation:

```python
class Trade(BaseModel):
    product_id: str      # Trading pair identifier
    price: float         # Trade price (must be positive)
    quantity: float      # Trade volume (cannot be negative)
    timestamp_ms: int    # Unix timestamp in milliseconds
```

#### Trade Validation Rules
- `product_id`: Cannot be empty or whitespace-only
- `price`: Must be positive (> 0)
- `quantity`: Cannot be negative (≥ 0)
- `timestamp_ms`: Must be within 24 hours past to 1 minute future tolerance

### Candle Model
Output candle with OHLCV relationship validation:

```python
class Candle(BaseModel):
    pair: str            # Trading pair
    open: float          # Opening price
    high: float          # Highest price in window
    low: float           # Lowest price in window
    close: float         # Closing price
    volume: float        # Total volume
    window_start_ms: int # Window start timestamp
    window_end_ms: int   # Window end timestamp
    candle_seconds: int  # Window duration
    schema_version: str  # Data schema version (default: "1.0")
```

#### Candle Validation Rules
- **Price Validation**: All OHLC prices must be positive
- **Volume Validation**: Volume cannot be negative
- **OHLC Relationships**: 
  - High ≥ Low
  - Low ≤ Open ≤ High
  - Low ≤ Close ≤ High
- **Window Validation**: End timestamp must be after start timestamp
- **Duration Validation**: `candle_seconds` must be positive

### Exception Handling
- **CandleError**: Base exception with optional context for debugging
- **Non-blocking Validation**: Trade validation issues log warnings but don't stop processing
- **Graceful Degradation**: Invalid candles return original data with error logging

## Stream Processing Details

### Reducer Functions

#### Candle Initialization
```python
def init_candle(trade: dict) -> dict:
    """Initialize OHLCV candle with first trade in window."""
    return {
        'open': float(trade['price']),
        'high': float(trade['price']),
        'low': float(trade['price']),
        'close': float(trade['price']),
        'volume': float(trade['quantity']),
        'pair': trade['product_id'],
    }
```

#### Candle Updates
```python  
def update_candle(candle: dict, trade: dict) -> dict:
    """Update candle state with new trade data."""
    price = float(trade['price'])
    quantity = float(trade['quantity'])
    
    candle['high'] = max(candle['high'], price)
    candle['low'] = min(candle['low'], price)
    candle['close'] = price  # Last trade becomes close
    candle['volume'] += quantity
    
    return candle
```

### Custom Timestamp Extraction
The service extracts timestamps from trade payloads rather than Kafka message timestamps to ensure accurate windowing regardless of message delivery delays.

## Configuration

The service uses Pydantic settings with comprehensive validation. All variables use the `CANDLES_` prefix:

### Application Settings
- `CANDLES_APP_NAME`: Service identifier (default: "candles")
- `CANDLES_DEBUG`: Enable debug mode (default: false)
- `CANDLES_LOG_LEVEL`: Logging level - DEBUG, INFO, WARNING, ERROR, CRITICAL (default: "INFO")
- `CANDLES_LOG_FORMAT`: Log format - "json" or "text" (default: "json")

### Kafka Settings
- `CANDLES_KAFKA_BROKER_ADDRESS`: Kafka broker connection in format "host:port" (default: "localhost:9092")
- `CANDLES_KAFKA_INPUT_TOPIC`: Input topic for trade messages (default: "trades")
- `CANDLES_KAFKA_OUTPUT_TOPIC`: Output topic for candle messages (default: "candles")
- `CANDLES_KAFKA_CONSUMER_GROUP`: Consumer group identifier (default: "candles_consumer_group")

### Processing Settings
- `CANDLES_CANDLE_SECONDS`: Candle window duration in seconds, 1-86400 range (default: 60)
- `CANDLES_PROCESSING_MODE`: Processing mode - "live" or "historical" (default: "live")

### Configuration Validation
- **App Name**: 1-100 alphanumeric characters, hyphens, underscores only
- **Broker Address**: Must match "host:port" pattern with valid port 1-65535
- **Topic Names**: 1-255 characters, alphanumeric/hyphens/underscores/dots, cannot start with . or _
- **Consumer Group**: 1-255 characters, alphanumeric/hyphens/underscores only
- **Candle Interval**: Must be between 1 second and 1 day (86400 seconds)
- **Production Warning**: Logs warning if production apps use DEBUG/INFO log levels

## Dependencies

The service requires the following Python packages (see `pyproject.toml` for exact versions):

- **quixstreams** (≥3.22.0): Stream processing framework with tumbling windows
- **pydantic** (≥2.11.7): Data validation and model serialization
- **pydantic-settings** (≥2.10.1): Environment variable configuration management
- **loguru** (≥0.7.3): Structured logging with JSON support

## Installation

```bash
# Install the candles service
cd services/candles
uv pip install -e .

# Or install all dependencies
uv pip install -r requirements.txt
```

## Usage

### Basic Usage
```bash
# Run with default configuration (live mode, 60-second candles)
python -m candles.main

# Or use the installed script
candles
```

### Live Mode Example
```bash
export CANDLES_PROCESSING_MODE=live
export CANDLES_KAFKA_INPUT_TOPIC=crypto-trades-live
export CANDLES_KAFKA_OUTPUT_TOPIC=crypto-candles-live
export CANDLES_CANDLE_SECONDS=30
python -m candles.main
```

### Historical Mode Example
```bash
export CANDLES_PROCESSING_MODE=historical
export CANDLES_KAFKA_INPUT_TOPIC=crypto-trades-historical
export CANDLES_KAFKA_OUTPUT_TOPIC=crypto-candles-historical
export CANDLES_CANDLE_SECONDS=300  # 5-minute candles
python -m candles.main
```

### Local Development Configuration
Create `src/candles/config/local.env`:
```bash
CANDLES_APP_NAME=candles-local
CANDLES_DEBUG=true
CANDLES_LOG_LEVEL=DEBUG
CANDLES_LOG_FORMAT=json

# Local development Kafka
CANDLES_KAFKA_BROKER_ADDRESS=localhost:31234
CANDLES_KAFKA_INPUT_TOPIC=trades-local
CANDLES_KAFKA_OUTPUT_TOPIC=candles-local
CANDLES_KAFKA_CONSUMER_GROUP=candles_local_group

# Faster candles for testing
CANDLES_CANDLE_SECONDS=30
CANDLES_PROCESSING_MODE=live
```

### Data Format Examples

#### Input Trade Format
```json
{
  "product_id": "BTC/USD",
  "price": 45000.50,
  "quantity": 0.1234,
  "timestamp_ms": 1640995200000
}
```

#### Output Candle Format
```json
{
  "pair": "BTC/USD",
  "open": "45000.50",
  "high": "45100.00",
  "low": "44950.25", 
  "close": "45075.30",
  "volume": "1.2345",
  "window_start_ms": 1640995200000,
  "window_end_ms": 1640995260000,
  "candle_seconds": 60,
  "schema_version": "1.0"
}
```

## Monitoring and Debugging

### Logging Levels
- **DEBUG**: Individual trade processing, candle updates, validation details
- **INFO**: Service startup, configuration summary, processing status
- **WARNING**: Non-fatal trade validation issues, production configuration warnings  
- **ERROR**: Critical candle validation failures, processing errors

### Debug Mode
Enable comprehensive logging for troubleshooting:
```bash
export CANDLES_DEBUG=true
export CANDLES_LOG_LEVEL=DEBUG
```

### Key Log Messages
- `"Starting candles service in {mode} mode..."`: Service startup confirmation
- `"Validated trade: {product_id}"`: Successful trade validation (DEBUG)
- `"Trade validation warning: {error}"`: Non-blocking validation issue (WARNING)
- `"Candle validation failed: {error}"`: Candle validation error (ERROR)
- `"Candle: {candle_data}"`: Individual candle output (DEBUG)

## Troubleshooting

### Common Issues

**Trade Validation Warnings**
- Check input data format matches expected Trade model
- Verify timestamp ranges (within 24 hours past to 1 minute future)
- Ensure price and quantity values are valid numbers
- These are non-blocking - service continues processing

**Candle Validation Failures**
- OHLC relationship violations indicate data corruption
- Check for negative prices or volumes in input trades
- Verify window timestamps are consistent
- Failed candles return original data for graceful degradation

**No Candles Produced**
- Verify input topic has trade data with correct format
- Check `timestamp_ms` field exists and contains valid timestamps
- Ensure candle interval matches your data frequency
- Review consumer group offset position

**Kafka Connection Issues**
- Verify `CANDLES_KAFKA_BROKER_ADDRESS` format and accessibility
- Ensure input/output topics exist or service has creation permissions
- Check consumer group doesn't have conflicting consumers
- Validate topic names follow Kafka naming conventions

**Performance Issues**
- Reduce `CANDLES_CANDLE_SECONDS` for faster updates (but higher throughput)
- Adjust Kafka consumer settings for batch processing
- Consider partitioning strategies for high-volume trading pairs
- Monitor memory usage with large candle windows

**Configuration Validation Errors**
- Verify environment variable names use `CANDLES_` prefix
- Check broker address format: "host:port" with valid port range
- Ensure topic names don't start with dots or underscores
- Validate candle interval is within 1-86400 seconds range

### Historical vs Live Mode
- **Historical**: Processes from beginning of topic (`auto_offset_reset=earliest`)
- **Live**: Processes from latest messages (default consumer behavior)
- **Mixed Processing**: Run historical mode first, then switch to live mode
- **Consistency**: Both modes use identical windowing and validation logic

## Integration

This service is part of the real-time ML trading system pipeline:
- **Upstream**: Receives trade data from the [Trades Service](../trades/README.md)
- **Downstream**: Feeds candle data to the [Technical Indicators Service](../technical_indicators/README.md)

## Development Setup

For complete development environment setup, Kubernetes cluster configuration, and project overview, see the main [project README](../../README.md).