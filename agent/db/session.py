"""Database session and engine configuration for PostgreSQL."""

import os
from contextlib import contextmanager
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Load environment variables if present
load_dotenv()

def get_database_url() -> str:
    """Build or retrieve database URL."""
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        # Normalize postgres:// to postgresql+psycopg:// if needed
        if env_url.startswith("postgres://"):
            return env_url.replace("postgres://", "postgresql+psycopg://", 1)
        if env_url.startswith("postgresql://") and not env_url.startswith("postgresql+"):
            return env_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return env_url

    pg_user = os.getenv("PGUSER", os.getenv("USER", "apple"))
    pg_host = os.getenv("PGHOST", "localhost")
    pg_port = os.getenv("PGPORT", "5432")
    pg_db = os.getenv("PGDATABASE", "stock_portfolio_intelligence")
    return f"postgresql+psycopg://{pg_user}@{pg_host}:{pg_port}/{pg_db}"


DATABASE_URL = get_database_url()

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for transactional database sessions.
    
    Usage:
        with get_db_session() as session:
            session.query(...)
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """Dependency generator for frameworks or standalone usage."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
