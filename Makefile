# Runs the trades service as a standalone Pyton app (not Dockerized)
dev:
	uv run services/${service}/src/${service}/main.py

# Builds and pushes the docker image to the given environment
build-and-push:
	./scripts/build-and-push-image.sh ${image} ${env}

# Deploys a service to the given environment
deploy:
	./scripts/deploy.sh ${service} ${env}

# Shuts down a service from the given environment
shutdown:
	./scripts/shutdown.sh ${service} ${env}


build-and-deploy:
	./scripts/build-and-push-image.sh ${image} ${env}
	./scripts/deploy.sh ${image} ${env}

lint:
	ruff check . --fix