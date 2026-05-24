# Backend

FastAPI service for authentication, task management, pricing, tracking, payouts, onboarding, and WhatsApp flows.

## Setup
```bash
pip install -r requirements.txt
cp ../.env.example ../.env
```

Run the API locally:
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Test
```bash
pytest tests -q
```

## Environment
- Keep backend secrets in the repo-root `.env`.
- Set `JWT_SECRET`, Supabase credentials, WhatsApp credentials, and `OPENAI_API_KEY` before starting production-like flows.

## Endpoints
The API is mounted under `/api/v1`.

- `POST /api/v1/auth/register/customer`
- `POST /api/v1/auth/register/worker`
- `POST /api/v1/auth/login`
- `POST /api/v1/tasks/create`
- `GET /api/v1/tasks/{task_id}`
- `PUT /api/v1/tasks/{task_id}`
- `GET /api/v1/workers/{worker_id}`
- `PUT /api/v1/workers/{worker_id}/location`
- `POST /api/v1/workers/{worker_id}/accept-task/{task_id}`
- `POST /api/v1/pricing/calculate`
- `GET /api/v1/payouts/worker/{worker_id}`
- `POST /api/v1/tracking/{task_id}/check-in`
- `POST /api/v1/tracking/{task_id}/check-out`
- `GET /api/v1/whatsapp/webhook`
- `POST /api/v1/whatsapp/webhook`

## Security notes
- Do not commit `.env` or any service-role keys.
- Rotate `JWT_SECRET` and API keys if they are ever exposed.
- Prefer least-privilege Supabase keys for local development.

## Docker quickstart

To run the full development stack (Postgres, Redis, backend, worker, beat, frontend) using docker-compose from the repo root:

```bash
# from repository root
docker compose up --build
```

The backend image installs all requirements (including `python-json-logger` and `prometheus_client`). The `backend/Dockerfile` performs a `pip install -r requirements.txt` during build.

If you only want to run the backend locally without Docker:

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Smoke test (local)

Build and run a disposable container and verify `/health` responds:

```bash
./scripts/docker_smoke_test.sh
```

This script builds the `eldercare-backend:smoke` image, runs a container, polls `/health`, and cleans up.

## Observability: Prometheus & Grafana

Prometheus scrape config example for a local Prometheus (add to `prometheus.yml`):

```yaml
scrape_configs:
	- job_name: 'eldercare-backend'
		static_configs:
			- targets: ['host.docker.internal:8000']
		metrics_path: /metrics
		scheme: http
```

Notes:
- When running via `docker compose`, Prometheus can scrape `eldercare-backend:8000` from inside the same compose network.
- A simple Grafana dashboard can visualize `http_requests_total` and `http_request_latency_seconds`.

Grafana starter: create a new dashboard and add these two panels:
- Panel 1: `sum(rate(http_requests_total[5m])) by (endpoint)`
- Panel 2: `histogram_quantile(0.95, sum(rate(http_request_latency_seconds_bucket[5m])) by (le, endpoint))`

## Production deployment notes

- The `docker-compose.prod.yml` file defines `postgres`, `redis`, `backend`, `worker`, and `beat` services. Use it for simple production-like deployments.
- The backend image runs an entrypoint that applies Alembic migrations on startup (no-op if `DATABASE_URL` is not set).
- Ensure secrets are provided (see `.env.example`) and never commit real secrets to the repo.
- The GitHub Actions CD workflow publishes images to GHCR; ensure `GITHUB_TOKEN` has `packages: write` (default in GitHub Actions) and set any additional secrets for production registries in repository settings.

Example deploy (compose + env file):

```bash
# create .env with production values
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

### Database backups

This repo includes a simple backup runner that performs a `pg_dump` and uploads the dump to S3 using `boto3`.

Environment variables required:
- `S3_BUCKET` (required)
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
- `BACKUP_INTERVAL_SECONDS` (optional, default: 86400 seconds / 1 day)

To enable backups with the production compose, set the S3 env vars in your `.env` and start the stack; the `db-backup` service runs continuously and uploads dumps to the configured bucket.

Restore a dump locally using:

```bash
# download the dump from S3, then
pg_restore -h localhost -p 5432 -U <user> -d <dbname> /path/to/pgdump-...dump
```

