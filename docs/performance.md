# Performance Notes

## Local Verification

- Backend tests: 53 passing.
- Frontend production bundle: about 273 KB before gzip, about 87 KB gzip.
- Docker Compose config validates without errors.

## Design Choices

- WhatsApp sends run through async service paths and Celery tasks where available.
- Task and worker listing endpoints are cacheable.
- Matching uses a bounded top-five ranking and avoids unbounded response sets.
- Health endpoints avoid slow work unless `/health/deep` is requested.

## Load Testing Target

The intended staging gate is:

- 500 concurrent task creation requests, p99 under 500 ms.
- 1000 concurrent WhatsApp webhook deliveries, p99 under 200 ms.
- 200 concurrent admin dashboard loads, p99 under 1 second.

The repo contains the operational hooks for those targets; a staging Locust run should be treated as release evidence, not a local laptop claim.
