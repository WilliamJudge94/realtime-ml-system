# Technical Indicators Service

A real-time technical indicators computation service that processes OHLCV candle streams and calculates various technical indicators using TA-Lib, with automatic RisingWave database integration for real-time analytics.

## Features

- **TA-Lib Integration**: Computes technical indicators using the industry-standard TA-Lib library
- **Stateful Stream Processing**: Maintains candle history in state for indicator calculations
- **RisingWave Integration**: Automatically creates and populates database tables for real-time SQL analytics  
- **Configurable History**: Maintains configurable number of candles in state for indicator computation
- **Multiple Indicators**: Supports RSI, MACD, Bollinger Bands, and other technical indicators
- **Real-time Processing**: Stream-based architecture for low-latency indicator updates
- **Robust Error Handling**: Comprehensive error handling with detailed logging and graceful degradation
- **Database Connectivity Testing**: Validates RisingWave connectivity before table creation

## Architecture

The service processes data through a 5-step pipeline:

1. **Ingestion**: Consumes OHLCV candle messages from Kafka input topic
2. **Filtering**: Filters candles by the specified time interval (candle_seconds)
3. **State Management**: Adds candles to stateful dictionary with configurable history limit
4. **Indicator Computation**: Computes technical indicators using TA-Lib from candle history
5. **Output**: Publishes computed indicators to Kafka output topic and RisingWave database

## Dependencies

- **ta-lib**: Technical Analysis Library for indicator calculations
- **numpy**: Numerical computing for efficient array operations
- **quixstreams**: Kafka streaming library for real-time data processing
- **psycopg2-binary**: PostgreSQL adapter for RisingWave connectivity
- **pydantic**: Data validation and configuration management
- **loguru**: Structured logging with comprehensive debugging
- **Python 3.13+**: Modern Python runtime

## Supported Technical Indicators

The service computes various technical indicators including:
- **RSI (Relative Strength Index)**: Momentum oscillator
- **MACD (Moving Average Convergence Divergence)**: Trend-following momentum indicator  
- **Bollinger Bands**: Volatility indicator with upper/lower bands
- **Moving Averages**: Simple and exponential moving averages
- **And more**: Extensible architecture supports additional TA-Lib indicators

## Data Models

### Input Candle Format
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

### Output Technical Indicator Format
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
  "rsi_14": 65.42,
  "macd": 125.30,
  "macd_signal": 120.15,
  "bollinger_upper": 45200.00,
  "bollinger_lower": 44800.00
}
```

## Configuration

### Kafka Configuration
- `KAFKA_BROKER_ADDRESS`: Kafka broker connection string
- `KAFKA_INPUT_TOPIC`: Input topic for candle messages
- `KAFKA_OUTPUT_TOPIC`: Output topic for technical indicator messages
- `KAFKA_CONSUMER_GROUP`: Consumer group identifier
- `CANDLE_SECONDS`: Time interval filter for candle processing

### Processing Configuration  
- `MAX_CANDLES_IN_STATE`: Maximum number of candles to maintain in state (for indicator calculations)

### RisingWave Database Configuration
- `RISINGWAVE_HOST`: RisingWave database host
- `RISINGWAVE_PORT`: RisingWave database port  
- `RISINGWAVE_USER`: Database username
- `RISINGWAVE_PASSWORD`: Database password
- `RISINGWAVE_DATABASE`: Target database name
- `TABLE_NAME_IN_RISINGWAVE`: Table name for indicator data

### Logging Configuration
- `LOG_LEVEL`: Logging verbosity level
- `DEBUG`: Enable debug mode for detailed processing logs

## RisingWave Integration

The service automatically:
1. **Tests Connectivity**: Validates RisingWave connection before starting
2. **Creates Tables**: Automatically creates the required table schema
3. **Configures Streaming**: Sets up Kafka-to-RisingWave streaming ingestion
4. **Enables Analytics**: Makes data available for real-time SQL queries

### Database Schema
```sql
CREATE TABLE technical_indicators (
    pair VARCHAR,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION, 
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    window_start_ms BIGINT,
    window_end_ms BIGINT,
    rsi_14 DOUBLE PRECISION,
    macd DOUBLE PRECISION,
    macd_signal DOUBLE PRECISION,
    bollinger_upper DOUBLE PRECISION,
    bollinger_lower DOUBLE PRECISION,
    -- Additional indicators as computed
);
```

## Usage

```bash
# Install dependencies (includes TA-Lib)
uv pip install -e .

# Run the service
python -m technical_indicators.main
```

## Monitoring and Debugging

The service provides extensive logging:
- **Initialization Logs**: RisingWave table creation and connectivity status
- **Processing Logs**: Candle state management and indicator computation
- **Error Logs**: Database connectivity issues and computation failures
- **Debug Logs**: Detailed per-message processing information

Monitor RisingWave integration:
```bash
# Query computed indicators
PGPASSWORD=123456 psql -h localhost -p 4567 -d dev -U root -c "SELECT * FROM technical_indicators ORDER BY window_start_ms DESC LIMIT 10;"
```

## Error Handling

The service handles various error conditions gracefully:
- **Database Connectivity Issues**: Service continues with Kafka-only mode if RisingWave is unavailable
- **Insufficient Data**: Skips indicator computation when not enough candles are available  
- **Computation Errors**: Logs errors and continues processing subsequent messages
- **Invalid Candle Data**: Validates input and handles malformed candle data

## Development Setup

For development environment setup, Kubernetes cluster configuration, and project overview, see the main [project README](../../README.md).

## Integration

This service is part of the real-time ML trading system pipeline:
- **Upstream**: Receives candle data from the [Candles Service](../candles/README.md)
- **Data Storage**: Integrates with RisingWave for real-time analytics and ML feature serving
- **Downstream**: Provides computed indicators for ML model training and inference