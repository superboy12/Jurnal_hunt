"""Database setup with SQLAlchemy supporting Prisma Postgres and SQLite fallback."""
import logging
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

logger = logging.getLogger(__name__)

db_url = settings.normalized_database_url
is_postgres = "postgresql" in db_url

try:
    if is_postgres:
        logger.info(f"Connecting to PostgreSQL database at {db_url.split('@')[-1]}...")
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=10,
            max_overflow=20,
            echo=False,
        )
        # Verify connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("PostgreSQL database connection established successfully!")
    else:
        raise ValueError("Using SQLite")
except Exception as e:
    logger.warning(f"PostgreSQL connection failed ({e}), falling back to SQLite: {settings.sqlite_fallback_url}")
    engine = create_engine(
        settings.sqlite_fallback_url,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
