#!/bin/bash

helm repo add grafana https://grafana.github.io/helm-charts
helm upgrade --install --create-namespace --wait grafana grafana/grafana --namespace=monitoring --values manifests/grafana-values.yaml