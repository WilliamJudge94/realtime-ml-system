#!/bin/bash

# This script is used to deploy a given service to the the given Kubernetes environment

service=$1
env=$2

if [ -z "$service" ]; then
    echo "Usage: $0 <service> <env>"
    exit 1
fi

if [ "$env" != "dev" ] && [ "$env" != "prod" ]; then
    echo "env must be either dev or prod"
    exit 1
fi

cd deployments/${env}

# hook the direnv tool here
# we add this line here so that direnv can load the right KUBECONFIG environment variable
# from the deployments/${env}/.env.local file
eval "$(direnv export bash)"
echo "KUBECONFIG=${KUBECONFIG}"

# if there is a kustomization.yaml file, use kustomize to deploy the service
if [ -f ${service}/kustomization.yaml ]; then
    echo "Deploying ${service} with kustomize"
    # delete the service
    # TODO: add the ignore-not-found flag to avoid errors the first time you deploy something
    kustomize build ${service} | kubectl delete -f -
    # deploy the service
    kustomize build ${service} | kubectl apply -f -
else
    # manually apply the deployment manifests
    kubectl create namespace rwml --dry-run=client -o yaml | kubectl apply -f -
    kubectl delete -f ${service}/${service}-d.yaml --ignore-not-found=true
    kubectl apply -f ${service}/${service}-d.yaml
fi