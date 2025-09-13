# Runs the trades service as a standalone Pyton app (not Dockerized)
dev:
	uv run services/${service}/src/${service}/main.py

# Builds and pushes the docker image to the given environment
build-and-push:
	./scripts/build-and-push-image.sh ${service} ${env}

# Deploys a service to the given environment
deploy:
	@if [ "${service}" = "trades" ] && [ -n "${variant}" ]; then \
		./scripts/deploy.sh trades_${variant} ${env}; \
	elif [ "${service}" = "candles" ] && [ -n "${variant}" ]; then \
		./scripts/deploy.sh candles_${variant} ${env}; \
	elif [ "${service}" = "technical_indicators" ] && [ -n "${variant}" ]; then \
		./scripts/deploy.sh technical_indicators_${variant} ${env}; \
	elif [ "${service}" = "predictions" ] && [ -n "${variant}" ]; then \
		./scripts/deploy.sh predictions_${variant} ${env}; \
	else \
		./scripts/deploy.sh ${service} ${env}; \
	fi

# Shuts down a service from the given environment
shutdown:
	@if [ "${service}" = "trades" ] && [ -n "${variant}" ]; then \
		./scripts/shutdown.sh trades_${variant} ${env}; \
	elif [ "${service}" = "candles" ] && [ -n "${variant}" ]; then \
		./scripts/shutdown.sh candles_${variant} ${env}; \
	elif [ "${service}" = "technical_indicators" ] && [ -n "${variant}" ]; then \
		./scripts/shutdown.sh technical_indicators_${variant} ${env}; \
	elif [ "${service}" = "predictions" ] && [ -n "${variant}" ]; then \
		./scripts/shutdown.sh predictions_${variant} ${env}; \
	else \
		./scripts/shutdown.sh ${service} ${env}; \
	fi


build-and-deploy:
	@if [ "${service}" = "trades" ] && [ -n "${variant}" ]; then \
		./scripts/build-and-push-image.sh trades ${env}; \
		./scripts/deploy.sh trades_${variant} ${env}; \
	elif [ "${service}" = "candles" ] && [ -n "${variant}" ]; then \
		./scripts/build-and-push-image.sh candles ${env}; \
		./scripts/deploy.sh candles_${variant} ${env}; \
	elif [ "${service}" = "technical_indicators" ] && [ -n "${variant}" ]; then \
		./scripts/build-and-push-image.sh technical_indicators ${env}; \
		./scripts/deploy.sh technical_indicators_${variant} ${env}; \
	elif [ "${service}" = "predictions" ] && [ "${variant}" = "training" ]; then \
		./scripts/build-and-push-image.sh predictions-training ${env}; \
		./scripts/deploy.sh predictions_${variant} ${env}; \
	elif [ "${service}" = "predictions" ] && [ "${variant}" = "live" ]; then \
		./scripts/build-and-push-image.sh predictions-live ${env}; \
		./scripts/deploy.sh predictions_${variant} ${env}; \
	elif [ "${service}" = "predictions" ] && [ -n "${variant}" ]; then \
		./scripts/build-and-push-image.sh predictions ${env}; \
		./scripts/deploy.sh predictions_${variant} ${env}; \
	else \
		./scripts/build-and-push-image.sh ${service} ${env}; \
		./scripts/deploy.sh ${service} ${env}; \
	fi

lint:
	ruff check . --fix

clean-docker:
	docker images -a | grep none | awk '{ print $3; }' | xargs docker rmi --force

port-kafka:
	kubectl -n kafka port-forward svc/kafka-ui 8182:8080

port-risingwave:
	kubectl port-forward -n risingwave service/risingwave 4567:4567

port-grafana:
	export POD_NAME=$$(kubectl get pods --namespace monitoring -l "app.kubernetes.io/name=grafana,app.kubernetes.io/instance=grafana" -o jsonpath="{.items[0].metadata.name}") && kubectl --namespace monitoring port-forward $$POD_NAME 3000

port-minio:
	kubectl port-forward -n risingwave service/risingwave-minio 9001:9001

port-mlflow:
	@echo "MLflow credentials:"
	@echo "Username: $$(kubectl get secret --namespace mlflow mlflow-tracking -o jsonpath="{ .data.admin-user }" | base64 -d)"
	@echo "Password: $$(kubectl get secret --namespace mlflow mlflow-tracking -o jsonpath="{.data.admin-password }" | base64 -d)"
	@echo "Starting port forward on http://localhost:5000"
	kubectl port-forward -n mlflow service/mlflow-tracking 5000:80

port-all:
	@echo "Starting all port forwards in parallel..."
	@echo "Kafka UI: http://localhost:8182"
	@echo "RisingWave: localhost:4567"
	@echo "Grafana: http://localhost:3000"
	@echo "MinIO: http://localhost:9001"
	@echo "MLflow: http://localhost:5000"
	@echo ""
	kubectl -n kafka port-forward svc/kafka-ui 8182:8080 & \
	kubectl port-forward -n risingwave service/risingwave 4567:4567 & \
	export POD_NAME=$$(kubectl get pods --namespace monitoring -l "app.kubernetes.io/name=grafana,app.kubernetes.io/instance=grafana" -o jsonpath="{.items[0].metadata.name}") && kubectl --namespace monitoring port-forward $$POD_NAME 3000 & \
	kubectl port-forward -n risingwave service/risingwave-minio 9001:9001 & \
	kubectl port-forward -n mlflow service/mlflow-tracking 5000:80 & \
	wait

# Orchestrated deployment: historical services first, then live services
# Usage: make orchestrated-deploy env=dev WAIT_MINUTES=2
WAIT_MINUTES ?= 2
orchestrated-deploy:
	@echo "=== Starting orchestrated deployment to ${env} environment ==="
	@echo "=== Step 1/11: Deploying trades historical ==="
	$(MAKE) build-and-deploy service=trades env=${env} variant=historical
	@echo "=== Step 2/11: Waiting ${WAIT_MINUTES} minutes ==="
	sleep $$(( ${WAIT_MINUTES} * 60 ))
	@echo "=== Step 3/11: Deploying candles historical ==="
	$(MAKE) build-and-deploy service=candles env=${env} variant=historical
	@echo "=== Step 4/11: Waiting ${WAIT_MINUTES} minutes ==="
	sleep $$(( ${WAIT_MINUTES} * 60 ))
	@echo "=== Step 5/11: Shutting down candles historical ==="
	$(MAKE) shutdown service=candles env=${env} variant=historical
	@echo "=== Step 6/11: Deploying technical_indicators historical ==="
	$(MAKE) build-and-deploy service=technical_indicators env=${env} variant=historical
	@echo "=== Step 7/11: Waiting ${WAIT_MINUTES} minutes ==="
	sleep $$(( ${WAIT_MINUTES} * 60 ))
	@echo "=== Step 8/11: Shutting down technical_indicators historical ==="
	$(MAKE) shutdown service=technical_indicators env=${env} variant=historical
	@echo "=== Step 9/11: Starting trades live ==="
	$(MAKE) build-and-deploy service=trades env=${env} variant=live
	@echo "=== Step 10/11: Starting candles live ==="
	$(MAKE) build-and-deploy service=candles env=${env} variant=live
	@echo "=== Step 11/11: Starting technical_indicators live ==="
	$(MAKE) build-and-deploy service=technical_indicators env=${env} variant=live
	@echo "=== Orchestrated deployment completed successfully! ==="
