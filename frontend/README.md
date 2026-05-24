# Frontend

React + TypeScript app for customers, workers, and admins.

## Setup
```bash
npm install
npm run dev
```

## Environment
- Local development can use `VITE_API_URL=http://localhost:8000/api/v1`.
- Docker/nginx deployments should use `VITE_API_URL=/api/v1`.

## Build and check
```bash
npm run build
npm run type-check
```

## App layout
- `src/pages/` — page routes
- `src/components/` — shared UI blocks
- `src/store/` — persisted client state
- `src/api/` — HTTP client and request helpers

## Notes
- The production frontend build is served through nginx in Docker.
- Tailwind configuration lives in `tailwind.config.ts`.
