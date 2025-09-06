# realtime-ml-system

## Development Container

This repository uses a dev container for consistent development environments.

### Base Setup
- **Base image**: `python:3.13-bookworm`
- **Installed tools**: uv, ruff, mypy, bandit, Docker-in-Docker, tmux, pre-commit, mise
- **Kubernetes tools**: kind, kubectl, helm, k9s, kustomize
- **VS Code extensions**: Python, Pylance, Jupyter, isort

### Post-Creation Commands
The `postCreateCommand.sh` script installs tools from `mise.toml` and sets up a Python virtual environment at `.venv`.

### Usage
1. Install the "Dev Containers" VS Code extension
2. Open this repo in VS Code
3. Click "Reopen in Container" when prompted

The container mounts SSH keys and automatically configures the development environment.

## Services

The system consists of several microservices for real-time data processing:

- **[Trades](services/trades/README.md)**: Kafka producer that fetches cryptocurrency trade data from Kraken's API via WebSocket (live) and REST API (historical), with configurable product pairs and JSON serialization
- **[Candles](services/candles/README.md)**: Real-time OHLCV candle aggregation service that processes trade streams using tumbling windows, with built-in validation and configurable time intervals
- **[Technical Indicators](services/technical_indicators/README.md)**: Computes technical indicators (RSI, MACD, Bollinger Bands, etc.) from candle streams using TA-Lib, with stateful processing and RisingWave database integration for real-time analytics. Supports both historical (Job) and live (Deployment) processing modes

## Local Kubernetes Development

The project includes scripts for setting up a local Kubernetes cluster with Kafka for development.

### Cluster Setup
- **Cluster name**: `rwml-34fa`
- **Network**: Custom Docker network (`172.100.0.0/16`)
- **Port mappings**: HTTP (80/443), Kafka brokers (9092, 31234-31236)

### Quick Start
```bash
cd deployments/dev/kind
./create_cluster.sh
```

This script:
1. Creates a kind cluster with custom networking
2. Installs Strimzi Kafka operator
3. Deploys Kafka cluster and UI

### Components
- **Kafka**: Deployed via Strimzi operator in `kafka` namespace
- **Kafka UI**: Web interface for managing Kafka topics and messages
- **Port forwarding**: Kafka accessible on `localhost:9092`

### Accessing Kafka UI
To access the Kafka UI web interface:
```bash
kubectl -n kafka port-forward svc/kafka-ui 8182:8080
```
Then visit `http://localhost:8182`

## Data Processing Setup

The system supports both historical data backfill and live streaming through a coordinated pipeline of microservices. This section explains how to properly set up and execute the data processing pipeline to ensure complete historical data coverage followed by seamless live processing.

### Pipeline Architecture

The data flows through a 3-service pipeline:
```
Trades (Historical/Live) → Candles (Historical/Live) → Technical Indicators
```

**Kafka Topics:**
- `trades-dev` - Raw trade data from Kraken API
- `candles-dev` - OHLCV candles aggregated from trades  
- `technical_indicators-dev` - Computed technical indicators

**Consumer Groups:**
- Candles Live: `candles_dev_live_group`
- Candles Historical: `candles_dev_historical_group`  
- Technical Indicators: `technical_indicators_dev_group`

### Execution Order

**Important:** Services must be started in the correct order to ensure proper data flow and avoid missing historical data.

#### Phase 1: Historical Data Processing

Execute these steps sequentially, waiting for each to complete before starting the next:

**1. Start Trades Historical Job**
```bash
make build-and-deploy service=trades env=dev variant=historical
```
- Runs as a Kubernetes Job (completes when finished)
- Fetches historical trade data from Kraken REST API
- Populates `trades-dev` topic with historical data
- ⏱️ **Wait for job completion** before proceeding

**2. Start Candles Historical Job**  
```bash
make build-and-deploy service=candles env=dev variant=historical
```
- Processes all historical trades from the beginning of the topic
- Uses `auto_offset_reset: earliest` to consume all available trades
- Generates historical candles in `candles-dev` topic
- ⏱️ **Wait for job completion** before proceeding

**3. Start Technical Indicators**
```bash
make build-and-deploy service=technical_indicators env=dev
```
- Processes historical candles and computes indicators
- Stores results in RisingWave database for querying
- Runs as a Deployment (continuous processing)
- ✅ **Keep running** for live processing

#### Phase 2: Live Data Processing

Once historical processing is complete, start live services:

**4. Start Trades Live**
```bash
make build-and-deploy service=trades env=dev variant=live
```
- Continuous WebSocket connection to Kraken for live trades
- Appends new trades to `trades-dev` topic
- Runs as a Deployment (continuous processing)

**5. Start Candles Live**
```bash
make build-and-deploy service=candles env=dev variant=live  
```
- Processes new live trades into candles
- Uses separate consumer group (`candles_dev_live_group`)
- Runs as a Deployment (continuous processing)

### Key Architecture Details

**Separate Consumer Groups**: Historical and live candles services use different consumer groups to avoid processing conflicts and ensure each mode processes appropriate data.

**Deployment Types**: 
- Historical services run as **Jobs** (run-to-completion)
- Live services run as **Deployments** (continuous processing)

**Mode Detection**: Services automatically detect `historical` vs `live` modes via the `variant` parameter and configure themselves accordingly.

**Data Storage**: Technical indicators are automatically stored in RisingWave database tables for real-time SQL queries and analytics.

**Gap Prevention**: This execution order ensures complete historical coverage with no data gaps when transitioning to live processing.

### Verification

Check that data is flowing correctly:

```bash
# Verify technical indicators in RisingWave
PGPASSWORD=123456 psql -h localhost -p 4567 -d dev -U root -c "SELECT pair, close, rsi_14, window_start_ms, to_timestamp(window_start_ms / 1000) as time FROM technical_indicators ORDER BY window_start_ms DESC LIMIT 10;"

# Check Kafka topics have data
kubectl -n kafka exec -it kafka-cluster-kafka-0 -- /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic trades-dev --from-beginning --max-messages 5
```