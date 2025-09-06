#!/bin/bash

# Remember to change the cluster name in the kind-with-portmapping.yaml file
CLUSTER_NAME="rwml-34fa"

# Steps:

# 1. Delete the cluster (if it exists, otherwise it will fail)
echo "Deleting the cluster..."
kind delete cluster --name $CLUSTER_NAME

# 2. Delete the docker network (if it exists, otherwise it will fail)
echo "Deleting the docker network..."
docker network rm ${CLUSTER_NAME}-network

# 3. Create the docker network
echo "Creating the docker network..."
docker network create --subnet 172.100.0.0/16 ${CLUSTER_NAME}-network

# 4. Create the cluster
echo "Creating the cluster..."
KIND_EXPERIMENTAL_DOCKER_NETWORK=${CLUSTER_NAME}-network kind create cluster --config ./kind-with-portmapping.yaml

# 5. Install Kafka
echo "Installing Kafka..."
chmod +x ./install_kafka.sh
./install_kafka.sh

# 6. Install Kafka UI
echo "Installing Kafka UI..."
chmod +x ./install_kafka_ui.sh
./install_kafka_ui.sh

# 7. Install RisingWave
echo "Installing RisingWave..."
chmod 755 ./install_risingwave.sh
./install_risingwave.sh

# 8. Install Grafana
echo "Installing Grafana..."
chmod +x ./install_grafana.sh
./install_grafana.sh

# 9. Install Grafana Dashboards
echo "Installing Grafana dashboards..."
kubectl apply -f ./manifests/grafana-dashboards-configmap.yaml