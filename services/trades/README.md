# Trades Service

A Kafka producer service that fetches cryptocurrency trade data from Kraken's API and publishes it to Kafka topics. The service supports both real-time (WebSocket) and historical (REST API) data collection modes with configurable trading pairs and robust error handling.

## Architecture

The trades service operates in two distinct modes:

### Live Mode (WebSocket)
- Connects to Kraken's WebSocket API (`wss://ws.kraken.com/v2`)
- Subscribes to real-time trade feeds for specified trading pairs
- Continuously streams trade data as it occurs
- Handles heartbeat messages and connection management
- Processes JSON responses with automatic error recovery

### Historical Mode (REST API)
- Fetches historical trade data via Kraken's REST API (`https://api.kraken.com/0/public/Trades`)
- Processes multiple trading pairs sequentially
- Configurable lookback period (last N days)
- Automatic pagination through timestamp-based queries
- Built-in retry logic with exponential backoff

Both modes produce standardized Trade objects that are serialized and published to Kafka topics with configurable partitioning.

## Trade Model

The `Trade` model represents a standardized cryptocurrency trade event:

```python
class Trade(BaseModel):
    product_id: str      # Trading pair (e.g., "BTC/USD")
    price: float         # Trade price
    quantity: float      # Trade volume/quantity
    timestamp: str       # ISO 8601 timestamp (e.g., "2025-04-24T11:35:42.856851Z")
    timestamp_ms: int    # Unix timestamp in milliseconds
```

### Key Methods
- `to_dict()`: Serialize trade to dictionary for Kafka publishing
- `from_kraken_websocket_response()`: Create from WebSocket API response
- `from_kraken_rest_api_response()`: Create from REST API response
- `unix_seconds_to_iso_format()`: Convert Unix timestamp to ISO format
- `iso_format_to_unix_seconds()`: Convert ISO format to Unix timestamp

## Configuration

The service uses Pydantic settings with environment variable support. All variables use the `TRADES_` prefix:

### Application Settings
- `TRADES_APP_NAME`: Service identifier (default: "trades")
- `TRADES_DEBUG`: Enable debug mode (default: false)
- `TRADES_LOG_LEVEL`: Logging level (default: "INFO")
- `TRADES_LOG_FORMAT`: Log format (default: "json")

### Kafka Settings
- `TRADES_KAFKA_BROKER_ADDRESS`: Kafka broker connection (default: "localhost:9092")
- `TRADES_KAFKA_TOPIC_NAME`: Target Kafka topic (default: "trades")
- `TRADES_KAFKA_TOPIC_PARTITIONS`: Number of topic partitions (default: 1)

### Trading Settings
- `TRADES_LIVE_OR_HISTORICAL`: Operation mode - "live" or "historical" (default: "live")
- `TRADES_PRODUCT_IDS`: List of trading pairs (default: ["BTC/USD"])
- `TRADES_LAST_N_DAYS`: Historical data lookback period (default: 1)

### Configuration Validation
- `live_or_historical`: Must be exactly "live" or "historical"
- `product_ids`: Cannot be empty, must match pattern `[A-Z0-9]{2,10}[\/\-]?[A-Z0-9]{2,10}`
- `last_n_days`: Must be positive when using historical mode

## Dependencies

The service requires the following Python packages (see `pyproject.toml` for exact versions):

- **quixstreams** (≥3.22.0): Kafka streaming library with built-in serialization
- **pydantic** (≥2.11.7): Data validation and settings management
- **loguru** (≥0.7.3): Structured logging with JSON support
- **websocket-client** (≥1.8.0): WebSocket connectivity for real-time data
- **requests**: HTTP client for REST API calls
- **pydantic-settings**: Environment variable configuration

## API Classes

### KrakenWebsocketAPI
Real-time data connector for live trading data:
- Maintains persistent WebSocket connection
- Automatically subscribes to specified trading pairs
- Handles heartbeat messages and connection recovery
- Returns continuous stream of Trade objects

### KrakenRestAPI
Historical data connector with intelligent pagination:
- Fetches historical trades for configurable time periods
- Processes multiple trading pairs sequentially
- Automatic timestamp progression and completion detection
- Built-in SSL error handling and retry mechanisms

## Installation

```bash
# Install the trades service
cd services/trades
uv pip install -e .

# Or install all dependencies
uv pip install -r requirements.txt
```

## Usage

### Basic Usage
```bash
# Run with default configuration (live BTC/USD data)
python -m trades.main

# Or use the installed script
trades
```

### Live Mode Example
```bash
export TRADES_LIVE_OR_HISTORICAL=live
export TRADES_PRODUCT_IDS='["BTC/USD", "ETH/USD", "ADA/USD"]'
export TRADES_KAFKA_TOPIC_NAME=crypto-trades-live
python -m trades.main
```

### Historical Mode Example
```bash
export TRADES_LIVE_OR_HISTORICAL=historical
export TRADES_PRODUCT_IDS='["BTC/USD", "ETH/USD"]'
export TRADES_LAST_N_DAYS=7
export TRADES_KAFKA_TOPIC_NAME=crypto-trades-historical
python -m trades.main
```

### Local Development Configuration
Create `src/trades/config/local.env`:
```bash
TRADES_APP_NAME=trades-local
TRADES_DEBUG=true
TRADES_LOG_LEVEL=DEBUG
TRADES_KAFKA_BROKER_ADDRESS=localhost:31234
TRADES_KAFKA_TOPIC_NAME=trades-local
TRADES_LIVE_OR_HISTORICAL=live
TRADES_PRODUCT_IDS=["BTC/USD", "ETH/USD"]
```

## Troubleshooting

### Common Issues

**WebSocket Connection Failures**
- Verify internet connectivity and firewall settings
- Check if `wss://ws.kraken.com/v2` is accessible
- Review logs for subscription confirmation messages

**REST API SSL Errors**
- The service includes automatic retry logic for SSL errors
- Wait for the retry delay (10 seconds) before manual intervention
- Verify system SSL certificates are up to date

**Invalid Trading Pairs**
- Ensure trading pairs match Kraken's supported symbols
- Use format like "BTC/USD", "ETH/EUR", "ADA/USDT"
- Check Kraken's API documentation for valid pair names

**Kafka Connection Issues**
- Verify `TRADES_KAFKA_BROKER_ADDRESS` points to accessible Kafka cluster
- Ensure topic exists or service has permissions to create topics
- Check Kafka cluster health and connectivity

**Configuration Validation Errors**
- Review environment variable names (must use `TRADES_` prefix)
- Validate JSON format for `TRADES_PRODUCT_IDS` array
- Ensure `TRADES_LAST_N_DAYS` is positive for historical mode

### Logging
The service uses structured JSON logging. Key log messages include:
- Trade data publication confirmations
- API connection status updates
- Configuration validation results
- Error conditions with retry attempts

## Development Setup

For complete development environment setup, Kubernetes cluster configuration, and project overview, see the main [project README](../../README.md).