Alert Automation Service

This small FastAPI service accepts Alertmanager webhooks at `/alert`, deduplicates alerts for a short TTL, and forwards them to Slack and PagerDuty when configured.

Environment variables

- `ALERT_SLACK_WEBHOOK`: Slack incoming webhook URL (optional)
- `PAGERDUTY_INTEGRATION_KEY`: PagerDuty Events v2 routing key (optional)
- `AUTOMATION_DEDUPE_TTL`: Deduplication TTL in seconds (default 300)

Run locally

```bash
python -m pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 5000
```

Docker

Build and run using the included `Dockerfile`:

```bash
docker build -t eldercare/automation:local .
docker run -e ALERT_SLACK_WEBHOOK="$ALERT_SLACK_WEBHOOK" -p 5000:5000 eldercare/automation:local
```

Compose

See `docker-compose.snippet.yml` for an example of how to attach the service to your existing compose stack.
