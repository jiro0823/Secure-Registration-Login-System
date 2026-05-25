from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import DATABASE_URL


def _ensure_mysql_database_exists() -> None:
    """Create the configured MySQL database if the local user has permission."""
    url = make_url(DATABASE_URL)
    database_name = url.database
    if not database_name:
        raise RuntimeError("DATABASE_URL must include a MySQL database name.")

    server_url = url.set(database=None)
    server_engine = create_engine(
        server_url, pool_pre_ping=True, isolation_level="AUTOCOMMIT")
    safe_database_name = database_name.replace("`", "``")
    with server_engine.connect() as connection:
        connection.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{safe_database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        )
    server_engine.dispose()


_ensure_mysql_database_exists()

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
