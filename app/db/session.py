import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

_raw_db_url = os.getenv("DATABASE_URL", "")

# Guard: only accept valid SQLAlchemy-compatible URLs (sqlite://, postgresql://, etc.)
# Supabase REST URLs (https://...) are NOT database DSNs — fall back to SQLite.
_VALID_PREFIXES = ("sqlite://", "postgresql://", "postgresql+psycopg2://", "postgres://")

if _raw_db_url and any(_raw_db_url.startswith(p) for p in _VALID_PREFIXES):
    DATABASE_URL = _raw_db_url
else:
    DATABASE_URL = "sqlite:///./node_api.db"

# Render/Heroku use "postgres://" scheme; SQLAlchemy 2.x requires "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# For SQLite, check_same_thread must be False for multithreaded requests
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator:
    """FastAPI dependency to provide a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all database tables on application startup."""
    from app.db import models  # noqa: F401
    Base.metadata.create_all(bind=engine)

