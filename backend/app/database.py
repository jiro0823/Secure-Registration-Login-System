from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import DATABASE_URL, DIRECT_URL


def _engine_options(database_url: str) -> dict:
    options = {
        "pool_pre_ping": True,
        "echo": False,
    }
    if "pooler.supabase.com:6543" in database_url:
        options["poolclass"] = NullPool
    return options

engine = create_engine(
    DATABASE_URL,
    **_engine_options(DATABASE_URL),
)

schema_engine = create_engine(
    DIRECT_URL or DATABASE_URL,
    **_engine_options(DIRECT_URL or DATABASE_URL),
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
