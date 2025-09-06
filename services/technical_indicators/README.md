# Technical Indicators Service

A real-time technical indicators computation service that processes OHLCV candle streams and calculates various technical indicators using TA-Lib, with automatic RisingWave database integration for real-time analytics and ML feature serving. The service supports both live and historical processing modes with sophisticated state management and error handling.

## Architecture

The technical indicators service implements a 5-step stateful stream processing pipeline:

### Processing Pipeline
1. **Ingestion**: Consumes OHLCV candle messages from Kafka input topic
2. **Filtering**: Filters candles by the specified time interval (`candle_seconds`)  
3. **State Management**: Adds candles to stateful dictionary with configurable history limit and intelligent window matching
4. **Indicator Computation**: Computes technical indicators using TA-Lib from maintained candle history
5. **Dual Output**: Publishes computed indicators to Kafka output topic and automatically ingests into RisingWave database

### Processing Modes

#### Live Mode (Default)
- Processes candle data in real-time as it arrives
- Uses Kafka consumer group with latest offset
- Maintains rolling candle history for continuous indicator computation
- Enables real-time ML feature serving and analytics

#### Historical Mode
- Processes historical candle data from beginning of topic
- Sets `auto_offset_reset=earliest` for complete data processing
- Sequentially processes all available candles while maintaining state
- Ideal for backtesting and historical ML feature generation

### Stateful Stream Processing
The service maintains sophisticated state management:
- **Candle History**: Maintains up to 70 candles per trading pair in memory
- **Window Matching**: Intelligently handles duplicate windows by updating existing candles
- **State Pruning**: Automatically removes oldest candles when history limit is reached
- **Pair Isolation**: Maintains separate state for each trading pair

## Technical Indicators

The service computes multiple categories of technical indicators with configurable periods:

### Moving Averages
- **Simple Moving Average (SMA)**: Configurable periods (default: 7, 14, 21, 60)
- **Exponential Moving Average (EMA)**: Configurable periods (default: 7, 14, 21, 60)

### Momentum Indicators
- **Relative Strength Index (RSI)**: Configurable periods (default: 7, 14, 21, 60)
- **MACD (Moving Average Convergence Divergence)**: Fast=7, Slow=14, Signal=9 periods

### Volume Indicators
- **On-Balance Volume (OBV)**: Momentum indicator using volume

### Data Requirements
- **Minimum Candles**: At least 2 candles required for any indicator computation
- **Period-Specific Requirements**: Each indicator requires minimum candles equal to its longest period
- **Graceful Handling**: Insufficient data results in indicator skipping with warning logs

### TA-Lib Integration
- Uses industry-standard TA-Lib library for all calculations
- Employs `stream` functions for real-time computation efficiency
- Handles NaN and infinite values automatically
- Provides numerical stability for production environments

## State Management

### Candle History Management
The service maintains intelligent candle state with the following logic:

```python
def update_candles_in_state(candle, state, settings):
    """
    Smart candle state management:
    - New time window: Append candle to history
    - Same time window: Replace existing candle (handles updates)
    - History overflow: Remove oldest candle (FIFO)
    """
```

### Window Matching Algorithm
```python
def are_same_window(candle, previous_candle):
    """
    Determines if two candles belong to same time window by checking:
    - Trading pair match
    - Identical window_start_ms
    - Identical window_end_ms
    """
```

### State Configuration
- **Maximum History**: Configurable via `max_candles_in_state` (default: 70)
- **Memory Management**: Automatic pruning when limit exceeded
- **Per-Pair State**: Independent state maintained for each trading pair

## Configuration

The service uses Pydantic settings with comprehensive validation. All variables use the `TECHNICAL_INDICATORS_` prefix:

### Application Settings
- `TECHNICAL_INDICATORS_APP_NAME`: Service identifier (default: "technical_indicators")
- `TECHNICAL_INDICATORS_DEBUG`: Enable debug mode (default: false)
- `TECHNICAL_INDICATORS_LOG_LEVEL`: Logging level - DEBUG, INFO, WARNING, ERROR, CRITICAL (default: "INFO")
- `TECHNICAL_INDICATORS_LOG_FORMAT`: Log format - "json" or "text" (default: "json")

### Kafka Settings
- `TECHNICAL_INDICATORS_KAFKA_BROKER_ADDRESS`: Kafka broker connection in format "host:port" (default: "localhost:9092")
- `TECHNICAL_INDICATORS_KAFKA_INPUT_TOPIC`: Input topic for candle messages (default: "candles")
- `TECHNICAL_INDICATORS_KAFKA_OUTPUT_TOPIC`: Output topic for indicator messages (default: "technical_indicators")
- `TECHNICAL_INDICATORS_KAFKA_CONSUMER_GROUP`: Consumer group identifier (default: "technical_indicators_consumer_group")

### Processing Settings
- `TECHNICAL_INDICATORS_CANDLE_SECONDS`: Candle interval filter, 1-86400 range (default: 60)
- `TECHNICAL_INDICATORS_MAX_CANDLES_IN_STATE`: Maximum candles in memory, 1-10000 range (default: 70)
- `TECHNICAL_INDICATORS_PROCESSING_MODE`: Processing mode - "live" or "historical" (default: "live")

### Indicator Configuration
- `TECHNICAL_INDICATORS_SMA_PERIODS`: SMA periods as comma-separated integers (default: "7,14,21,60")
- `TECHNICAL_INDICATORS_EMA_PERIODS`: EMA periods as comma-separated integers (default: "7,14,21,60")
- `TECHNICAL_INDICATORS_RSI_PERIODS`: RSI periods as comma-separated integers (default: "7,14,21,60")

### RisingWave Settings
- `TECHNICAL_INDICATORS_RISINGWAVE_HOST`: RisingWave database host (default: "localhost")
- `TECHNICAL_INDICATORS_RISINGWAVE_PORT`: RisingWave database port, 1-65535 range (default: 4567)
- `TECHNICAL_INDICATORS_RISINGWAVE_USER`: Database username, 1-63 characters (default: "root")
- `TECHNICAL_INDICATORS_RISINGWAVE_PASSWORD`: Database password (default: "")
- `TECHNICAL_INDICATORS_RISINGWAVE_DATABASE`: Target database name, 1-63 characters (default: "dev")
- `TECHNICAL_INDICATORS_TABLE_NAME_IN_RISINGWAVE`: Table name for indicators, must start with letter (default: "technical_indicators")

### Configuration Validation
- **App Name**: 1-100 characters, alphanumeric/hyphens/underscores only
- **Broker Address**: Must match "host:port" pattern with valid port range
- **Topic Names**: 1-255 characters, cannot start with dots or underscores
- **Periods**: Must be positive integers, automatically sorted and deduplicated
- **Table Name**: Must start with letter, contain only alphanumeric and underscores
- **Production Warning**: Logs warning if production apps use DEBUG/INFO log levels

## RisingWave Integration

The service provides seamless integration with RisingWave for real-time analytics:

### Automatic Setup Process
1. **Connectivity Testing**: Validates RisingWave connection before table creation
2. **Table Creation**: Automatically creates table schema with all indicator columns
3. **Kafka Connector**: Configures Kafka-to-RisingWave streaming ingestion
4. **Error Handling**: Gracefully handles RisingWave unavailability

### Database Schema
The service automatically creates the following table structure:

```sql
CREATE TABLE technical_indicators (
    pair VARCHAR,
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume FLOAT,
    window_start_ms BIGINT,
    window_end_ms BIGINT,
    candle_seconds INT,
    sma_7 FLOAT,
    sma_14 FLOAT,
    sma_21 FLOAT,
    sma_60 FLOAT,
    ema_7 FLOAT,
    ema_14 FLOAT,
    ema_21 FLOAT,
    ema_60 FLOAT,
    rsi_7 FLOAT,
    rsi_14 FLOAT,
    rsi_21 FLOAT,
    rsi_60 FLOAT,
    macd_7 FLOAT,
    macdsignal_7 FLOAT,
    macdhist_7 FLOAT,
    obv FLOAT,
    PRIMARY KEY (pair, window_start_ms, window_end_ms)
) WITH (
    connector='kafka',
    topic='technical_indicators',
    properties.bootstrap.server='localhost:9092'
) FORMAT PLAIN ENCODE JSON;
```

### Key Features
- **Primary Key Design**: Prevents duplicates using (pair, window_start_ms, window_end_ms)
- **Automatic Ingestion**: RisingWave automatically consumes from Kafka topic
- **Real-time Updates**: Data becomes available for queries immediately
- **JSON Format**: Native support for JSON message format from Kafka

## Dependencies

The service requires the following Python packages (see `pyproject.toml` for exact versions):

- **ta-lib**: Industry-standard Technical Analysis Library for indicator calculations
- **numpy**: Numerical computing foundation for TA-Lib array operations
- **quixstreams** (≥3.22.0): Stream processing framework with stateful operations
- **psycopg2-binary**: PostgreSQL adapter for RisingWave database connectivity
- **pydantic** (≥2.11.7): Data validation and model serialization
- **pydantic-settings** (≥2.10.1): Environment variable configuration management
- **loguru** (≥0.7.3): Structured logging with comprehensive debugging support

### TA-Lib Installation Note
TA-Lib requires system-level installation. On most systems:
```bash
# Ubuntu/Debian
sudo apt-get install ta-lib

# macOS
brew install ta-lib

# Or use conda
conda install -c conda-forge ta-lib
```

## Installation

```bash
# Install the technical indicators service
cd services/technical_indicators
uv pip install -e .

# Or install all dependencies
uv pip install -r requirements.txt
```

## Usage

### Basic Usage
```bash
# Run with default configuration (live mode, 60-second candles)
python -m technical_indicators.main

# Or use the installed script
technical_indicators
```

### Live Mode Example
```bash
export TECHNICAL_INDICATORS_PROCESSING_MODE=live
export TECHNICAL_INDICATORS_KAFKA_INPUT_TOPIC=crypto-candles-live
export TECHNICAL_INDICATORS_KAFKA_OUTPUT_TOPIC=crypto-indicators-live
export TECHNICAL_INDICATORS_CANDLE_SECONDS=60
export TECHNICAL_INDICATORS_SMA_PERIODS="5,10,20,50"
python -m technical_indicators.main
```

### Historical Mode Example
```bash
export TECHNICAL_INDICATORS_PROCESSING_MODE=historical
export TECHNICAL_INDICATORS_KAFKA_INPUT_TOPIC=crypto-candles-historical
export TECHNICAL_INDICATORS_KAFKA_OUTPUT_TOPIC=crypto-indicators-historical
export TECHNICAL_INDICATORS_MAX_CANDLES_IN_STATE=100
python -m technical_indicators.main
```

### Local Development Configuration
Create `src/technical_indicators/config/local.env`:
```bash
# Application settings
TECHNICAL_INDICATORS_APP_NAME=technical_indicators-local
TECHNICAL_INDICATORS_DEBUG=true
TECHNICAL_INDICATORS_LOG_LEVEL=DEBUG
TECHNICAL_INDICATORS_LOG_FORMAT=json

# Kafka settings
TECHNICAL_INDICATORS_KAFKA_BROKER_ADDRESS=localhost:31234
TECHNICAL_INDICATORS_KAFKA_INPUT_TOPIC=candles-local
TECHNICAL_INDICATORS_KAFKA_OUTPUT_TOPIC=technical_indicators-local
TECHNICAL_INDICATORS_KAFKA_CONSUMER_GROUP=technical_indicators_local_group

# Technical Indicators specific settings
TECHNICAL_INDICATORS_CANDLE_SECONDS=30
TECHNICAL_INDICATORS_MAX_CANDLES_IN_STATE=70

# RisingWave connection settings
TECHNICAL_INDICATORS_RISINGWAVE_HOST=localhost
TECHNICAL_INDICATORS_RISINGWAVE_PORT=4567
TECHNICAL_INDICATORS_RISINGWAVE_USER=root
TECHNICAL_INDICATORS_RISINGWAVE_PASSWORD=
TECHNICAL_INDICATORS_RISINGWAVE_DATABASE=dev

# Indicator periods configuration
TECHNICAL_INDICATORS_SMA_PERIODS=7,14,21,60
TECHNICAL_INDICATORS_EMA_PERIODS=7,14,21,60
TECHNICAL_INDICATORS_RSI_PERIODS=7,14,21,60
```

### Data Format Examples

#### Input Candle Format
```json
{
  "pair": "BTC/USD",
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

#### Output Technical Indicator Format
```json
{
  "pair": "BTC/USD",
  "open": 45000.50,
  "high": 45100.00,
  "low": 44950.25,
  "close": 45075.30,
  "volume": 1.2345,
  "window_start_ms": 1640995200000,
  "window_end_ms": 1640995260000,
  "candle_seconds": 60,
  "sma_7": 44985.32,
  "sma_14": 44972.18,
  "sma_21": 44958.95,
  "ema_7": 44990.45,
  "ema_14": 44976.82,
  "rsi_14": 65.42,
  "macd_7": 125.30,
  "macdsignal_7": 120.15,
  "macdhist_7": 5.15,
  "obv": 12345.67
}
```

## RisingWave Querying

### Real-time Analytics Examples
```bash
# Query latest indicators for all pairs
PGPASSWORD=123456 psql -h localhost -p 4567 -d dev -U root -c "
SELECT pair, close, rsi_14, sma_21, macd_7 
FROM technical_indicators 
ORDER BY window_start_ms DESC 
LIMIT 10;"

# Get RSI signals for specific trading pair
PGPASSWORD=123456 psql -h localhost -p 4567 -d dev -U root -c "
SELECT window_start_ms, close, rsi_14,
       CASE 
         WHEN rsi_14 > 70 THEN 'OVERBOUGHT'
         WHEN rsi_14 < 30 THEN 'OVERSOLD'
         ELSE 'NEUTRAL'
       END as rsi_signal
FROM technical_indicators 
WHERE pair = 'BTC/USD'
ORDER BY window_start_ms DESC 
LIMIT 20;"

# Moving average crossover analysis
PGPASSWORD=123456 psql -h localhost -p 4567 -d dev -U root -c "
SELECT window_start_ms, pair, close, sma_7, sma_21,
       CASE WHEN sma_7 > sma_21 THEN 'BULLISH' ELSE 'BEARISH' END as trend
FROM technical_indicators 
WHERE pair IN ('BTC/USD', 'ETH/USD')
ORDER BY pair, window_start_ms DESC;"

# Table statistics and health check
PGPASSWORD=123456 psql -h localhost -p 4567 -d dev -U root -c "
SELECT 
    COUNT(*) as total_rows,
    COUNT(DISTINCT pair) as unique_pairs,
    MIN(window_start_ms) as earliest_data,
    MAX(window_start_ms) as latest_data
FROM technical_indicators;"
```

## Monitoring and Debugging

### Logging Levels
- **DEBUG**: Individual candle processing, state management, indicator calculations
- **INFO**: Service startup, configuration summary, RisingWave connection status
- **WARNING**: Insufficient data warnings, production configuration notices
- **ERROR**: RisingWave connectivity failures, TA-Lib calculation errors

### Debug Mode
Enable comprehensive logging for troubleshooting:
```bash
export TECHNICAL_INDICATORS_DEBUG=true
export TECHNICAL_INDICATORS_LOG_LEVEL=DEBUG
```

### Key Log Messages
- `"Starting technical indicators service..."`: Service startup confirmation
- `"Number of candles in state: {count}"`: State management tracking (DEBUG)
- `"Insufficient data for technical indicators"`: Minimum data requirement warning
- `"RisingWave connectivity test PASSED/FAILED"`: Database connection status
- `"Successfully created table '{name}' in RisingWave"`: Table initialization success
- `"Technical indicator: {data}"`: Individual indicator output (DEBUG)

### RisingWave Monitoring
```bash
# Check table exists and row count
PGPASSWORD=123456 psql -h localhost -p 4567 -d dev -U root -c "
SELECT 
    table_name,
    (SELECT COUNT(*) FROM technical_indicators) as row_count
FROM information_schema.tables 
WHERE table_name = 'technical_indicators';"

# Monitor recent data ingestion
PGPASSWORD=123456 psql -h localhost -p 4567 -d dev -U root -c "
SELECT pair, COUNT(*) as indicator_count, MAX(window_start_ms) as latest_data
FROM technical_indicators 
GROUP BY pair 
ORDER BY latest_data DESC;"
```

## Troubleshooting

### Common Issues

**RisingWave Connectivity Failures**
- Verify RisingWave is running and accessible at configured host:port
- Check network connectivity and firewall settings
- Validate database credentials and permissions
- Service continues with Kafka-only mode if RisingWave unavailable

**Insufficient Data Warnings**
- Normal during startup - service needs minimum candles for calculations
- Check input topic has adequate candle history
- Verify `max_candles_in_state` is sufficient for largest indicator period
- Review `candle_seconds` filter matches input data interval

**TA-Lib Calculation Errors**
- Ensure TA-Lib is properly installed at system level
- Check for NaN or infinite values in input candle data
- Verify candle data contains required fields (open, high, low, close, volume)
- Review candle data for logical OHLC relationships

**No Indicators Produced**
- Verify input topic contains candle data matching `candle_seconds` filter
- Check consumer group offset position
- Ensure minimum 2 candles in state before indicators computed
- Review logs for validation errors in input candle format

**State Management Issues**
- Monitor state size with DEBUG logging
- Adjust `max_candles_in_state` based on indicator periods and memory constraints
- Verify window matching logic handles candle updates correctly
- Check for memory leaks with long-running processes

**Kafka Connection Issues**
- Verify `TECHNICAL_INDICATORS_KAFKA_BROKER_ADDRESS` format and accessibility
- Ensure input/output topics exist or service has creation permissions
- Check consumer group doesn't have conflicting consumers
- Validate topic names follow Kafka naming conventions

**Performance Optimization**
- Increase `max_candles_in_state` for more stable indicator calculations
- Reduce indicator periods or types for lower computational overhead
- Consider consumer group parallelization for high-volume trading pairs
- Monitor memory usage and adjust based on data volume

**Configuration Validation Errors**
- Verify environment variable names use `TECHNICAL_INDICATORS_` prefix
- Check periods configuration format: comma-separated positive integers
- Ensure RisingWave connection parameters are within valid ranges
- Validate table name follows PostgreSQL identifier rules

### Historical vs Live Mode
- **Historical**: Processes from beginning of topic for complete backtesting
- **Live**: Processes latest data for real-time ML feature serving
- **State Consistency**: Both modes maintain identical indicator calculation logic
- **RisingWave**: Both modes populate same table structure for unified analytics

## Integration

This service is a critical component of the real-time ML trading system pipeline:
- **Upstream**: Receives OHLCV candle data from the [Candles Service](../candles/README.md)
- **Database**: Integrates with RisingWave for real-time SQL analytics and complex event processing
- **Downstream**: Provides computed technical indicators for ML model training, backtesting, and real-time inference
- **Analytics**: Enables real-time trading signals, risk management, and portfolio optimization

## Development Setup

For complete development environment setup, Kubernetes cluster configuration, and project overview, see the main [project README](../../README.md).