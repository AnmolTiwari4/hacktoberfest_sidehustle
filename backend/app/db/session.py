"""SQLAlchemy engine, session dependency, and shared declarative base."""

import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()


def _database_url() -> str:
    raw_url = os.getenv("DATABASE_URL") or "sqlite:///./marketscout.db"
    url = raw_url.strip().strip("\"'").strip()
    # A common PowerShell/.env copy-paste mistake stores the full assignment as
    # the value (DATABASE_URL=DATABASE_URL=sqlite:///...). Unwrap it safely.
    while url.upper().startswith("DATABASE_URL="):
        url = url.split("=", 1)[1].strip().strip("\"'").strip()
    if not url:
        url = "sqlite:///./marketscout.db"

    # Render and other providers may supply the legacy postgres:// scheme.
    if url.startswith("postgres://"):
        url = "postgresql+psycopg2://" + url[len("postgres://") :]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://") :]

    try:
        make_url(url)
    except Exception as exc:
        raise ValueError(
            "DATABASE_URL is invalid. Use sqlite:///./marketscout.db locally, "
            "or a valid postgresql://user:password@host:5432/database URL."
        ) from exc
    return url


DATABASE_URL = _database_url()
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """Yield one short-lived database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
