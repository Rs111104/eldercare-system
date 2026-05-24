#!/usr/bin/env bash
set -euo pipefail

# Sends a test alert payload to local Alertmanager
ALERTMANAGER=${ALERTMANAGER:-http://localhost:9093}

curl -XPOST -d '[{"labels": {"alertname": "TestAlert", "severity": "warning"}, "annotations": {"summary": "Test alert from CI"}}]' \
  -H "Content-Type: application/json" ${ALERTMANAGER}/api/v1/alerts

echo "Sent test alert to ${ALERTMANAGER}"
