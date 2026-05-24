#!/usr/bin/env bash
set -euo pipefail

IMAGE_TAG=eldercare-backend:smoke
CONTAINER_NAME=eldercare-smoke-test

echo "Building backend image (${IMAGE_TAG})..."
docker build -t ${IMAGE_TAG} -f backend/Dockerfile backend

echo "Starting container..."
docker run -d --name ${CONTAINER_NAME} -p 8000:8000 ${IMAGE_TAG}

# wait for /health to return 200 up to 60s
for i in $(seq 1 30); do
  if curl -sS -f http://127.0.0.1:8000/health >/dev/null 2>&1; then
    echo "Health check OK"
    docker stop ${CONTAINER_NAME} >/dev/null
    docker rm ${CONTAINER_NAME} >/dev/null
    echo "Smoke test succeeded"
    exit 0
  fi
  echo "Waiting for service to become healthy... ($i)"
  sleep 2
done

echo "Service did not become healthy in time"
docker logs ${CONTAINER_NAME} || true
docker stop ${CONTAINER_NAME} || true
docker rm ${CONTAINER_NAME} || true
exit 2
