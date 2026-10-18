# MarketScout AI

MarketScout AI helps small businesses research a local market, discover and score prospects, and turn evidence into a practical 7/30/90-day growth plan. The backend is FastAPI with SQLAlchemy 2.x; the dashboard is Streamlit.

## Features

- Business profile creation and editing.
- Market research from Google Search and Google Maps results through SerpAPI, with cited sources and Groq-generated structured summaries.
- Deterministic 100-point lead fit scoring: industry (40), geography (25), activity evidence (20), and freshness/completeness (15).
- Lead status and notes management with CSV export.
- Evidence-grounded growth actions for the next 7, 30, and 90 days.
- PostgreSQL JSONB in production and SQLite JSON for local development.

## Local setup

1. Use Python 3.10 or newer and create a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and set `SERPAPI_KEY` and `GROQ_API_KEY`.
4. Start the API from the project root: `uvicorn app.main:app --app-dir backend --reload`.
5. Start the dashboard in another terminal: `streamlit run frontend/app.py`.
6. Open `http://localhost:8501`. The API health endpoint is `http://127.0.0.1:8000/health` and OpenAPI docs are at `/docs`.

The application uses `DATABASE_URL` from the environment and creates missing tables on startup for a fresh MVP deployment. Alembic configuration is included for managed schema changes.

## Deployment and API address

Deploy the `backend/` application to Render with the start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (set Render's root directory to `backend/`, or run `uvicorn app.main:app --app-dir backend` from the project root), and set `DATABASE_URL`, `SERPAPI_KEY`, `GROQ_API_KEY`, `GROQ_MODEL`, and `CORS_ORIGINS` in Render's environment. Use a managed PostgreSQL database for persistent production data.

Deploy the Streamlit app from `frontend/app.py`. In Streamlit Cloud, add `API_BASE_URL = "https://your-service.onrender.com"` to the app's Secrets, replacing it with the public HTTPS URL assigned to the Render backend, and set the backend `CORS_ORIGINS` to the Streamlit app origin. The URL is intentionally configured through settings because no deployed Render service URL is included in this project.

## API routes

All feature routes are under `/api/v1`:

- `POST /businesses`, `GET /businesses`, `GET/PATCH /businesses/{id}`
- `POST /research`, `GET /research/{id}`, `GET /research/{id}/report`
- `POST /leads/search`, `GET /leads`, `GET/PATCH /leads/{id}`, `GET /leads/export`
- `POST /growth-plans`, `GET /growth-plans/{id}`
- `GET /health`

## Secrets

Keep provider keys in environment variables or the ignored local `.env` file. Never commit `.env`; use `.env.example` as the blank template.
