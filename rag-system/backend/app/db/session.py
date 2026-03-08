"""
Database Session Management

Uses SQLite for local persistence. The database file is stored at data/app.db
and persists across server restarts.

SQLAlchemy is configured with:
- check_same_thread=False: Required for FastAPI's async nature
- echo=False in production: Set to True for SQL debugging
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

from app.config import settings

# Ensure data directory exists
os.makedirs(settings.data_dir, exist_ok=True)

# SQLite database URL - file stored in data/app.db
DATABASE_URL = f"sqlite:///{settings.database_path}"

# Create engine with SQLite-specific settings
# check_same_thread=False is required for SQLite with FastAPI
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=settings.debug  # Log SQL statements in debug mode
)

# Session factory - creates new sessions for each request
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for all ORM models
Base = declarative_base()


def get_db():
    """
    Dependency that provides a database session.

    Usage in FastAPI:
        @router.get("/")
        def endpoint(db: Session = Depends(get_db)):
            ...

    The session is automatically closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize the database by creating all tables.

    Called during application startup in main.py.
    Safe to call multiple times - only creates tables that don't exist.
    """
    # Import all models to ensure they're registered with Base
    from app.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
