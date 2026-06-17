import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Always load backend/.env (not cwd) so OPENAI_API_KEY + DATABASE_URL work from any working directory
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_BACKEND_ROOT / ".env")
load_dotenv()  # optional overrides from process cwd


def _normalize_database_url(raw_url: str) -> str:
    url = (raw_url or "").strip()
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://") :]
    return url


DATABASE_URL = _normalize_database_url(
    os.getenv("DATABASE_URL") or os.getenv("NEON_URL") or ""
)
engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None
SessionLocal = (
    sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
)
Base = declarative_base()


def get_db():
    if SessionLocal is None:
        raise HTTPException(
            status_code=503,
            detail="Database is not configured. Set DATABASE_URL in environment variables.",
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
