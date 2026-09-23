from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from app.core.config import DB_USER, DB_PASSWORD, DB_NAME


# Synchronous database setup
engine = create_engine(
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@localhost:5432/{DB_NAME}",
    echo=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


# Asynchronous database setup
async_engine = create_async_engine(
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@localhost:5432/{DB_NAME}",
    echo=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)