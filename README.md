# ElderCare System

Full-stack eldercare service platform with a FastAPI backend, React + Vite frontend, and PostgreSQL/Supabase migrations.

## Repo layout
- `backend/` — API, test suite, and service logic
- `frontend/` — customer, worker, and admin UI
- `database/` — SQL migrations, seed data, and helper functions
- `docker-compose.yml` — local multi-container stack

## Quick start
1. Copy the environment template:
```bash
cp .env.example .env
```
2. Fill in the required secrets in `.env`.
3. Start the stack:
```bash
docker compose up --build
```

## Local URLs
- Backend API: `http://localhost:8000`
- Backend docs: `http://localhost:8000/docs`
- Frontend app: `http://localhost:3000`

## Verification
```bash
cd backend
pytest tests -q

cd ../frontend
npm run build
```

## Environment notes
- Keep `.env` out of source control.
- Use a strong `JWT_SECRET` in every non-local environment.
- Set `VITE_API_URL=/api/v1` when serving the frontend behind nginx or Docker.

## Docs
- [Backend setup](backend/README.md)
- [Frontend setup](frontend/README.md)
- [Database setup](database/README.md)
- [API reference](API_REFERENCE.md)
- [Deployment guide](DEPLOYMENT.md)
