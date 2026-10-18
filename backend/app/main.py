"""FastAPI entrypoint for the MarketScout AI API."""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import businesses, growth_plans, leads, research
from app.db import models  # noqa: F401 - register all mapped tables
from app.db.session import Base, engine

load_dotenv()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Alembic is available for controlled deployments; create_all makes first-run MVP setup immediate.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="MarketScout AI API", version="1.0.0", lifespan=lifespan)
origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501").split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["GET", "POST", "PATCH", "OPTIONS"], allow_headers=["*"])

for route in (businesses.router, research.router, leads.router, growth_plans.router):
    app.include_router(route, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "marketscout-ai"}
