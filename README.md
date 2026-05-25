# ElderCare System

WhatsApp-first eldercare coordination for families who need a reliable helper, not another app to learn.

The system lets a customer request help through WhatsApp or the web, matches the task to a verified worker, tracks the visit, records the task history, and splits the worker payout with an audit trail. The interesting parts are the care-specific workflow: multilingual conversation state, scored worker matching, guarded task transitions, payout holds for disputes, operational metrics, and tests for hostile input.

## What To Review First

- `backend/app/services/conversation_engine.py` — WhatsApp state machine with English, Tamil, and Hindi replies.
- `backend/app/services/matching_engine.py` — explainable worker ranking by distance, rating, availability, and experience.
- `backend/app/store.py` — in-memory production harness used by the local stack and tests.
- `frontend/src/pages/TaskCreate.tsx` — customer task request flow.
- `docs/adr/0001-whatsapp-first-care-flow.md` — why the product starts in WhatsApp.

## Run It

```bash
cp .env.example .env
docker compose up --build
```

Local URLs:

- Frontend: `http://localhost:3000`
- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

For a local demo, keep provider keys blank. WhatsApp and OpenAI calls fall back to safe local behavior instead of blocking the app.

## Verify It

```bash
python -m pytest backend/tests
python -m compileall backend/app backend/tests

cd frontend
npm run lint
npm run type-check
npm run build
npm audit --audit-level=high
```

Security checks:

```bash
pip-audit -r backend/requirements.txt
bandit -q -r backend/app --severity-level high
```

## Architecture

```text
backend/app
  routers/        HTTP boundaries and auth checks
  services/       business rules and integrations
  core/           config, logging, auth, metrics, cache
  models/         request and response schemas
  store.py        local data store used by tests and compose

frontend/src
  api/            authenticated API client
  components/     reusable UI
  pages/          route-level screens
  store/          session state
```

## Care Workflow

1. Customer sends a WhatsApp/web request.
2. The conversation engine collects service type, details, and confirmation.
3. The matching engine ranks verified workers and logs the decision.
4. A worker accepts, checks in, completes the task, and earns a split payout.
5. The customer rates the task. Low ratings hold payout and flag the task.
6. Admins review anomalies, dead letters, payout holds, and audit records.

## Production Notes

- Set a strong `JWT_SECRET`.
- Set `WHATSAPP_APP_SECRET` before accepting webhooks.
- Keep `WHATSAPP_ACCESS_TOKEN`, `OPENAI_API_KEY`, and payment keys in environment variables only.
- Run behind HTTPS.
- Treat phone numbers, addresses, and care notes as PII.

More detail lives in `docs/`: architecture decisions, schema notes, threat model, and performance notes.
