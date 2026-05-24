# Incident Runbook — ElderCare Platform

This runbook outlines first-response steps for common incidents and escalation paths.

## 1. High-level severity definitions
- Sev 1 (Critical): Service down or data-loss impacting all users.
- Sev 2 (Major): Significant functionality degraded for many users.
- Sev 3 (Minor): Partial impact or single-tenant issue.

## 2. Initial triage
1. Confirm alert in Prometheus / Alertmanager and check `up` and `/metrics`.
2. Check recent deploys (GitHub Actions runs) and Docker stack status.
3. Check Redis, Postgres, and worker logs.

## 3. Common checks
- Backend 500s: tail `backend` logs; search for stack traces; restart service if needed.
- Database connection errors: check `postgres` container, run `pg_isready`, inspect connection counts.
- Worker queue backlog: check Redis list length `LRANGE whatsapp:queue 0 -1` and Celery worker status.

## 4. Mitigation steps
- Scale workers (docker compose scale worker=2) or restart failing containers.
- Rollback to previous image if a recent deploy caused regression.

## 5. Escalation
- For Sev 1: notify on-call via Slack/PagerDuty and call the engineering lead.
- For Sev 2: notify team channel and assign an engineer.

## 6. Postmortem
- Create incident ticket with timeline, root cause, remediation, and action items.
- Add follow-up tasks to improve monitoring or add automation.

