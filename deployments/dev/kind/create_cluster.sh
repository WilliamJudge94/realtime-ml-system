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