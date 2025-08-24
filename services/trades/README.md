# Trades Service

A Kafka producer service that fetches cryptocurrency trade data from Kraken's API and publishes it to Kafka topics.

## Features

- **Data Sources**: Supports both live (WebSocket) and historical (REST API) data from Kraken
- **Kafka Integration**: Publishes trade events with JSON serialization
- **Configurable**: Supports multiple product pairs and topic partitioning
- **Trade Model**: Structured trade data with timestamp conversion utilities

## Dependencies

- **quixstreams**: Kafka streaming library
- **pydantic**: Data validation and serialization
- **loguru**: Structured logging
- **websocket-client**: WebSocket connectivity

## Usage

```bash
# Install dependencies
uv pip install -e .

# Run the service
python -m trades.main
```

The service configuration is managed through environment variables and the config module.

## Development Setup

For development environment setup, Kubernetes cluster configuration, and project overview, see the main [project README](../../README.md).