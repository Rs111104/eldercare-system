# Recent Backend Changes

This file summarizes the recent fixes and recommended next steps.

## Summary of Fixes

- Fixed pricing calculation to safely handle `floor_price` and `ceiling_price` when configuration values are `None` (prevented `float(None)` errors).
- Restored legacy behavior in task creation: `customer_id` is now optional. If omitted, the authenticated user's id is used; if a provided `customer_id` doesn't exist, a minimal (ghost) customer record is created to maintain backward compatibility with existing integrations.

## Files Modified

- `app/store.py` — safe handling for `floor_price` and `ceiling_price` in `calculate_pricing_breakdown()`
- `app/routers/tasks.py` — `create_task` now accepts optional `customer_id` and recreates a minimal customer record when necessary

## Tests Run

All backend tests were executed locally; results:

- `cd backend && pytest -q` => `26 passed, 4 warnings`

## Recommended Next Steps

1. Add an Alembic migration to add `role` column to the `refresh_tokens` table if you plan to use the DB-backed refresh token store in production.

2. Run frontend unit tests and linting, and migrate any auth state to the centralized `useStore` as planned.

3. Create a minimal deployment smoke test (docker-compose or local dev) that starts backend and frontend and runs basic healthchecks.

4. Add CI (GitHub Actions) that runs `pytest` for backend and `npm test` / `vite build` for frontend on pull requests.

## Quick Commands

Run backend tests:

```bash
cd backend
pytest -q
```

Run the frontend dev server (from repo root):

```bash
cd frontend
npm install
npm run dev
```

Start both services with Docker Compose (if configured):

```bash
docker-compose up --build
```

## Notes

- If you want, I can add the Alembic migration file and update `alembic/versions/` with a migration to add the `role` column to the `refresh_tokens` table.
- I can also open a PR including these changes and the changelog, and prepare a GitHub Actions workflow to run tests on push/PR.
