"""
Self-contained database setup for the service.

Database connection variables are loaded from environment variables
(.env via python-dotenv). For this student project, default values are
provided explicitly so the service runs out of the box.
"""
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from .logging_config import get_logger

load_dotenv()
logger = get_logger(__name__)

# --- Explicit DB variables (student project, defaults are fine) -------------
DB_USERNAME = os.getenv("DB_USERNAME", "pasinozavr")
DB_PASSWORD = os.getenv("DB_PASSWORD", "61YcGTqd")
DB_SERVER = os.getenv("DB_SERVER", "tcp:cloud2026.database.windows.net").replace("tcp:", "")
DB_DATABASE = os.getenv("DB_DATABASE", "pr2")
ODBC_DRIVER = os.getenv("ODBC_DRIVER", "ODBC Driver 17 for SQL Server")
# ---------------------------------------------------------------------------

Base = declarative_base()


def build_connection_url() -> str:
    # Allow tests / local dev to bypass Azure SQL by providing
    # a full DATABASE_URL (e.g. sqlite:///:memory:).
    override = os.getenv("DATABASE_URL")
    if override:
        logger.debug("Using DATABASE_URL override: %s", override)
        return override

    odbc = (
        f"Driver={{{ODBC_DRIVER}}};"
        f"Server=tcp:{DB_SERVER},1433;"
        f"Database={DB_DATABASE};"
        f"Uid={DB_USERNAME};"
        f"Pwd={DB_PASSWORD};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )
    logger.debug("Building DB connection URL for server=%s db=%s", DB_SERVER, DB_DATABASE)
    return f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc)}"


DATABASE_URL = build_connection_url()

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema(schema_name: str) -> None:
    logger.info("Ensuring schema '%s' exists", schema_name)
    with engine.begin() as conn:
        conn.execute(text(
            f"IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = '{schema_name}') "
            f"EXEC('CREATE SCHEMA {schema_name}')"
        ))
    logger.debug("Schema '%s' check completed", schema_name)
