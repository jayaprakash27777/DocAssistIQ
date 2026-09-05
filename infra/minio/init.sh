#!/bin/sh
# DocAssistIQ — MinIO bucket initialization script.
# Runs after MinIO starts to create the application bucket.
# Executed by the minio-init one-shot service in docker-compose.yml.

set -e

MINIO_ALIAS="local"
BUCKET_NAME="${OBJECT_STORAGE_BUCKET:-docassistiq}"
MINIO_ENDPOINT="${OBJECT_STORAGE_ENDPOINT:-http://minio:9000}"
MINIO_ACCESS_KEY="${OBJECT_STORAGE_ACCESS_KEY:-minioadmin}"
MINIO_SECRET_KEY="${OBJECT_STORAGE_SECRET_KEY:-minioadmin}"

echo "Waiting for MinIO to become ready..."
until mc alias set "${MINIO_ALIAS}" "${MINIO_ENDPOINT}" "${MINIO_ACCESS_KEY}" "${MINIO_SECRET_KEY}" 2>/dev/null; do
  sleep 2
done
echo "MinIO is ready."

# Create bucket if it does not exist
if mc ls "${MINIO_ALIAS}/${BUCKET_NAME}" > /dev/null 2>&1; then
  echo "Bucket '${BUCKET_NAME}' already exists."
else
  mc mb "${MINIO_ALIAS}/${BUCKET_NAME}"
  echo "Bucket '${BUCKET_NAME}' created."
fi
