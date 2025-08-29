# Technical Indicators Service Restructuring Todo

## Overview
Restructure the `@services/technical_indicators/` service to match the consistent patterns used in `@services/candles/` and `@services/trades/` services.

## Directory Structure Changes

### 1. Create `config/` Directory Structure
- [ ] Create `src/technical_indicators/config/` directory
- [ ] Move `config.py` to `src/technical_indicators/config/config.py`
- [ ] Create `src/technical_indicators/config/local.env` file for environment variables
- [ ] Create `src/technical_indicators/config/validators.py` for configuration validation
- [ ] Create `src/technical_indicators/config/__init__.py`

### 2. Create `models/` Directory Structure  
- [ ] Create `src/technical_indicators/models/` directory
- [ ] Create `src/technical_indicators/models/__init__.py`
- [ ] Create `src/technical_indicators/models/technical_indicator.py` model class
- [ ] Create `src/technical_indicators/models/exceptions.py` for custom exceptions

## Configuration Updates

### 3. Update `pyproject.toml`
- [ ] Add missing dependencies:
  - `loguru>=0.7.3`
  - `pydantic>=2.11.7` 
  - `pydantic-settings>=2.10.1`
  - `quixstreams>=3.22.0`
  - `talib` (existing technical analysis library)
- [ ] Fix entry point naming from `technical-indicators` to `technical_indicators` for consistency
- [ ] Update build system if needed to match pattern

### 4. Refactor Configuration System
- [ ] Update config to use proper env file path: `Path(__file__).parent / "local.env"`
- [ ] Add env prefix: `TECHNICAL_INDICATORS_`
- [ ] Add comprehensive field validation similar to candles/trades services
- [ ] Add logging configuration (app_name, debug, log_level, log_format)
- [ ] Add Kafka configuration validation
- [ ] Add technical indicators specific configuration validation
- [ ] Remove hardcoded config instantiation and print statement

## Code Structure Updates

### 5. Update `__init__.py`
- [ ] Replace `hello()` function with proper `main()` function
- [ ] Import and use the new config system properly
- [ ] Match the pattern used in other services

### 6. Update `main.py`
- [ ] Refactor to use the new config structure: `from technical_indicators.config.config import load_settings`
- [ ] Add proper error handling and logging setup similar to candles service
- [ ] Add configuration logging on startup
- [ ] Add graceful shutdown handling (KeyboardInterrupt, Exception)
- [ ] Match the overall structure pattern used in other services

### 7. Update Import Statements
- [ ] Fix all import statements in `candle.py` to use new config path
- [ ] Fix all import statements in `indicators.py` if needed
- [ ] Fix all import statements in `main.py` to use new package structure
- [ ] Update any other files that import from the old structure

## Docker & Deployment Infrastructure

### 8. Create Docker Support
- [ ] Create `docker/technical_indicators.Dockerfile` following candles/trades pattern
- [ ] Use `ghcr.io/astral-sh/uv:python3.12-bookworm-slim` as base image
- [ ] Set proper CMD to run technical indicators main.py
- [ ] Follow same build pattern as other services

### 9. Create Development Deployments
- [ ] Create `deployments/dev/technical_indicators/` directory
- [ ] Create `deployments/dev/technical_indicators/technical_indicators-d.yaml`
- [ ] Configure environment variables:
  - `TECHNICAL_INDICATORS_APP_NAME=technical_indicators-dev`
  - `TECHNICAL_INDICATORS_KAFKA_BROKER_ADDRESS=kafka-e11b-kafka-bootstrap.kafka.svc.cluster.local:9092`
  - `TECHNICAL_INDICATORS_KAFKA_INPUT_TOPIC=candles-dev`
  - `TECHNICAL_INDICATORS_KAFKA_OUTPUT_TOPIC=technical_indicators-dev`
  - `TECHNICAL_INDICATORS_KAFKA_CONSUMER_GROUP=technical_indicators_dev_group`
- [ ] Set appropriate replica count and resource limits
- [ ] Use `technical_indicators:dev` image with `imagePullPolicy: Never`

### 10. Create Production Deployments
- [ ] Create `deployments/prod/technical_indicators/` directory
- [ ] Create `deployments/prod/technical_indicators/technical_indicators-d.yaml`
- [ ] Configure production environment variables:
  - `TECHNICAL_INDICATORS_APP_NAME=technical_indicators-prod`
  - `TECHNICAL_INDICATORS_KAFKA_INPUT_TOPIC=candles-prod`
  - `TECHNICAL_INDICATORS_KAFKA_OUTPUT_TOPIC=technical_indicators-prod`
  - `TECHNICAL_INDICATORS_KAFKA_CONSUMER_GROUP=technical_indicators_prod_group`
- [ ] Use production image: `ghcr.io/williamjudge94/technical_indicators:latest`
- [ ] Set `imagePullPolicy: Always`
- [ ] Add proper resource requests and limits
- [ ] Set namespace to `rwml`

## Files to be Created/Modified

### New Files to Create:
- `src/technical_indicators/config/__init__.py`
- `src/technical_indicators/config/local.env`
- `src/technical_indicators/config/validators.py`
- `src/technical_indicators/models/__init__.py`
- `src/technical_indicators/models/technical_indicator.py`
- `src/technical_indicators/models/exceptions.py`
- `docker/technical_indicators.Dockerfile`
- `deployments/dev/technical_indicators/technical_indicators-d.yaml`
- `deployments/prod/technical_indicators/technical_indicators-d.yaml`

### Files to Modify:
- `pyproject.toml` - dependencies and entry points
- `src/technical_indicators/config.py` - move to config/config.py and restructure
- `src/technical_indicators/__init__.py` - add proper main() function
- `src/technical_indicators/main.py` - update imports and error handling
- `src/technical_indicators/candle.py` - update config imports
- `src/technical_indicators/indicators.py` - verify/update imports if needed

## Success Criteria
- [ ] Directory structure matches candles/trades services
- [ ] Configuration system follows established patterns
- [ ] All imports work correctly
- [ ] Service can be started using consistent entry point
- [ ] Error handling and logging match other services
- [ ] Dependencies are properly managed
- [ ] Docker image builds successfully and follows established patterns
- [ ] Kubernetes deployment files are properly configured for dev and prod environments
- [ ] Service can be deployed and communicate via Kafka topics
- [ ] Integration with candles service works (consumes candles, produces technical indicators)

## Notes
- This restructuring ensures consistency across all services
- Maintains existing functionality while improving maintainability
- Follows established patterns for easier onboarding and maintenance