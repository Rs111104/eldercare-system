#!/usr/bin/env bash
set -euo pipefail
SERVICE=${SERVICE:-http://localhost:5000}

curl -XPOST -d '[{"labels": {"alertname": "DirectTestAlert", "severity": "warning", "instance": "local"}, "annotations": {"summary": "Direct test alert"}}]' \
  -H "Content-Type: application/json" ${SERVICE}/alert

echo "Sent direct alert to ${SERVICE}" 
