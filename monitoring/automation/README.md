Automation integration

This folder contains examples and guidance for automated responders that receive Alertmanager webhooks and trigger actions (Slack, PagerDuty, runbooks).

Suggested architecture

- Alertmanager routes critical alerts to the `pagerduty` receiver (PagerDuty integration key).
- Alertmanager routes other alerts to a `automation` webhook which posts to an internal automation service.
- The automation service can:
  - Post rich messages to Slack (using a bot token)
  - Create incidents in PagerDuty using Events API v2
  - Trigger remediation scripts (scale workers, restart services) via CI/CD APIs

Security

- Keep webhook URLs and integration keys in your secret manager (do not commit them).
- Use `SECRETS_PROVIDER` (we added AWS Secrets Manager support) to inject secrets into the runtime.

Test alert (manual)

To send a test alert to Alertmanager (assumes Alertmanager is reachable at http://localhost:9093):

```bash
curl -XPOST -d '[{"labels": {"alertname": "TestAlert", "severity": "warning"}, "annotations": {"summary": "Test alert"}}]' \
  -H "Content-Type: application/json" http://localhost:9093/api/v1/alerts
```

Automation service example

You can implement a small service that listens on `/alert` and acts on incoming alerts. Keep it minimal and idempotent.
