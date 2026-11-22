"""
Database Connection Manager
Provides secure SQLAlchemy engine and raw PyMySQL connections to MySQL 8.0.
Guarantees password masking in logs and safe connection testing.
"""

from urllib.parse import quote_plus
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from src.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from src.utils.logger import setup_logger

logger = setup_logger("db_connection")

def get_db_url(include_database: bool = True) -> str:
    """Builds a secure SQLAlchemy connection URL."""
    encoded_password = quote_plus(DB_PASSWORD)
    db_part = f"/{DB_NAME}" if include_database else ""
    return f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}{db_part}?charset=utf8mb4"

def get_masked_url(include_database: bool = True) -> str:
    """Returns a safe, masked URL for logs without exposing the password."""
    db_part = f"/{DB_NAME}" if include_database else ""
    return f"mysql+pymysql://{DB_USER}:***@{DB_HOST}:{DB_PORT}{db_part}"

def get_engine(include_database: bool = True) -> Engine:
    """Creates a SQLAlchemy engine."""
    url = get_db_url(include_database=include_database)
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False
    )

def test_connection() -> bool:
    """Tests basic connectivity to MySQL server and reports status without leaking credentials."""
    logger.info(f"Testing connection to MySQL at {get_masked_url(include_database=False)}...")
    try:
        engine = get_engine(include_database=False)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT VERSION();")).scalar()
            logger.info(f"Successfully connected to MySQL! Server Version: {result}")
            return True
    except Exception as e:
        logger.error(f"Failed to connect to MySQL: {type(e).__name__} - {str(e)}")
        return False
