import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. Load .env file for local development if available
def _load_env_file():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        # Fallback minimal parser when python-dotenv is not installed
        root_dir = Path(__file__).resolve().parent.parent
        env_file = root_dir / ".env"
        if env_file.is_file():
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            if k not in os.environ:
                                os.environ[k] = v
            except Exception:
                pass

_load_env_file()

# 2. Resolve database URL from environment variables
# Neon / Vercel integrations commonly use DATABASE_URL or POSTGRES_URL
def get_database_url() -> str:
    candidates = [
        "DATABASE_URL",
        "POSTGRES_URL",
        "SQLALCHEMY_DATABASE_URL",
        "DATABASE_URL_UNPOOLED",
        "POSTGRES_URL_NON_POOLING",
    ]
    for key in candidates:
        val = os.getenv(key)
        if val and val.strip():
            return val.strip()
    return ""


# 3. Detect production / Vercel runtime
is_vercel = bool(os.getenv("VERCEL") or os.getenv("VERCEL_ENV"))
is_production = (
    is_vercel
    or os.getenv("ENVIRONMENT", "").lower() in ("production", "prod")
    or os.getenv("ENV", "").lower() in ("production", "prod")
    or os.getenv("VERCEL_ENV", "").lower() in ("production", "preview")
)

raw_url = get_database_url()

if is_production:
    if not raw_url:
        raise RuntimeError(
            "Production/Vercel environment detected, but no database connection string was found. "
            "Please ensure DATABASE_URL or POSTGRES_URL is configured in your Vercel project environment variables. "
            "SQLite fallback is disallowed in production to prevent read-only filesystem errors."
        )
    if raw_url.startswith("sqlite"):
        raise RuntimeError(
            "Production/Vercel environment detected, but a SQLite database URL was provided. "
            "Vercel serverless functions have a read-only filesystem; Neon PostgreSQL (DATABASE_URL) is required."
        )
else:
    if not raw_url:
        # Default to local SQLite for local development only
        raw_url = "sqlite:///./sql_app.db"

# 4. Normalize PostgreSQL URL scheme for SQLAlchemy
# SQLAlchemy 1.4+ deprecated postgres:// in favor of postgresql://
if raw_url.startswith("postgres://"):
    raw_url = raw_url.replace("postgres://", "postgresql://", 1)

# Ensure SSL mode is set if using Neon PostgreSQL without sslmode query parameter
if "neon.tech" in raw_url and "sslmode" not in raw_url:
    separator = "&" if "?" in raw_url else "?"
    raw_url = f"{raw_url}{separator}sslmode=require"

SQLALCHEMY_DATABASE_URL = raw_url

# 5. Configure SQLAlchemy engine based on database dialect
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    # Neon PostgreSQL (Vercel Serverless Function friendly settings)
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,  # Check connection liveness to handle severed serverless connections
        pool_recycle=300,    # Recycle connections after 5 minutes
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
