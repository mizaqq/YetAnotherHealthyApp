Dev quickstart

Backend (FastAPI):

1. Create venv and install deps:

```
cd apps/backend
uv sync
```

2. Run API:

```
uv run uvicorn app.main:app --reload --port 8000
```

Frontend (React + Vite + Tailwind):

1. Install node deps:

```
cd apps/frontend
npm install
```

2. Run dev server:

```
npm run dev
```

Vite dev server proxies API requests to `http://localhost:8000` via `/api/*`.

Sample health check page is wired to `/api/v1/health`.
