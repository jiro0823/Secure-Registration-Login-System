from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import DATABASE_URL


engine_options = {
    "pool_pre_ping": True,
    "echo": False,
}

if "pooler.supabase.com:6543" in DATABASE_URL:
    engine_options["poolclass"] = NullPool

engine = create_engine(
    DATABASE_URL,
    **engine_options,
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
