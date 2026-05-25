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
_schema_initialized = False


class Base(DeclarativeBase):
    pass


def init_schema() -> None:
    global _schema_initialized
    if _schema_initialized:
        return
    Base.metadata.create_all(bind=schema_engine)
    _schema_initialized = True


def get_db():

    init_schema()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
