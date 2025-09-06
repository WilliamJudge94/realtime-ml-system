# apply secret for minio access
kubectl apply --recursive -f deployments/dev/kind/manifests/mlflow_minio_secret.yaml

# install mlflow
helm upgrade --install --create-namespace --wait mlflow oci://registry-1.docker.io/bitnamicharts/mlflow --namespace=mlflow --values deployments/dev/kind/manifests/mlflow_values.yaml