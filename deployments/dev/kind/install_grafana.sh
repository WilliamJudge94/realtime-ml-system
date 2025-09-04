#!/bin/bash

# Apply dashboard ConfigMaps first
kubectl apply -f manifests/grafana-dashboards-configmap.yaml

helm repo add grafana https://grafana.github.io/helm-charts
helm upgrade --install --create-namespace --wait grafana grafana/grafana --namespace=monitoring --values manifests/grafana-values.yaml


# export POD_NAME=$(kubectl get pods --namespace monitoring -l "app.kubernetes.io/name=grafana,app.kubernetes.io/instance=grafana" -o jsonpath="{.items[0].metadata.name}")
# kubectl --namespace monitoring port-forward $POD_NAME 3000