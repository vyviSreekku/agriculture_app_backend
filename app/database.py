from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import settings
from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine_kwargs = {"pool_pre_ping": True}

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    # Needed for SQLite when used with FastAPI dependency injection
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=naming_convention)
Base = declarative_base(metadata=metadata)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
