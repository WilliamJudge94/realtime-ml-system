# install mlflow
helm upgrade --install --create-namespace --wait mlflow oci://registry-1.docker.io/bitnamicharts/mlflow --namespace=mlflow --values ./manifests/mlflow-values.yaml

# apply secret for minio access
kubectl apply -f ./manifests/mlflow_minio_secret.yaml