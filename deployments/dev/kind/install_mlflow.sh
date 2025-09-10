# setup postgresql for mlflow
echo "Setting up PostgreSQL databases and user for MLflow..."
kubectl exec risingwave-postgresql-0 -n risingwave -- env PGPASSWORD=postgres psql -U postgres -c "DO \$\$ BEGIN CREATE USER mlflow WITH PASSWORD 'mlflow'; EXCEPTION WHEN duplicate_object THEN RAISE NOTICE 'User already exists'; END \$\$;"
kubectl exec risingwave-postgresql-0 -n risingwave -- env PGPASSWORD=postgres psql -U postgres -c "CREATE DATABASE mlflow OWNER mlflow;" || echo "Database mlflow may already exist"
kubectl exec risingwave-postgresql-0 -n risingwave -- env PGPASSWORD=postgres psql -U postgres -c "CREATE DATABASE mlflow_auth OWNER mlflow;" || echo "Database mlflow_auth may already exist"
kubectl exec risingwave-postgresql-0 -n risingwave -- env PGPASSWORD=postgres psql -U postgres -d mlflow -c "GRANT ALL PRIVILEGES ON DATABASE mlflow TO mlflow;" 2>/dev/null || true
kubectl exec risingwave-postgresql-0 -n risingwave -- env PGPASSWORD=postgres psql -U postgres -d mlflow_auth -c "GRANT ALL PRIVILEGES ON DATABASE mlflow_auth TO mlflow;" 2>/dev/null || true

# create namespace first
kubectl create namespace mlflow --dry-run=client -o yaml | kubectl apply -f -

# apply secret for minio access (before helm install)
kubectl apply -f ./manifests/mlflow_minio_secret.yaml

# install mlflow
helm upgrade --install --create-namespace --wait mlflow oci://registry-1.docker.io/bitnamicharts/mlflow --namespace=mlflow --values ./manifests/mlflow-values.yaml