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

- **[Trades](services/trades/README.md)**: Kafka producer that fetches cryptocurrency trade data from Kraken's API
- **[Candles](services/candles/README.md)**: Candle data processing service

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