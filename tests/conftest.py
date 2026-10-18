"""Isolated in-memory API fixtures."""

from contextlib import asynccontextmanager
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.db import models  # noqa: F401
from app.db.session import Base, get_db
from app.main import app


@pytest.fixture
def test_session_factory():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    yield factory
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(test_session_factory):
    def override_get_db():
        with test_session_factory() as db:
            yield db

    @asynccontextmanager
    async def no_database_lifespan(_app):
        yield

    app.dependency_overrides[get_db] = override_get_db
    app.router.lifespan_context = no_database_lifespan
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
