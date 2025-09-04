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
	else \
		./scripts/deploy.sh ${service} ${env}; \
	fi

# Shuts down a service from the given environment
shutdown:
	@if [ "${service}" = "trades" ] && [ -n "${variant}" ]; then \
		./scripts/shutdown.sh trades_${variant} ${env}; \
	else \
		./scripts/shutdown.sh ${service} ${env}; \
	fi


build-and-deploy:
	@if [ "${service}" = "trades" ] && [ -n "${variant}" ]; then \
		./scripts/build-and-push-image.sh trades ${env}; \
		./scripts/deploy.sh trades_${variant} ${env}; \
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

port-grafana:
	export POD_NAME=$$(kubectl get pods --namespace monitoring -l "app.kubernetes.io/name=grafana,app.kubernetes.io/instance=grafana" -o jsonpath="{.items[0].metadata.name}") && kubectl --namespace monitoring port-forward $$POD_NAME 3000

port-minio:
	kubectl port-forward -n risingwave service/risingwave-minio 9001:9001
port-risingwave:
	kubectl port-forward -n risingwave service/risingwave 4567:4567