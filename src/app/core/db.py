from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core import config

from .vec import create_vec_table, register_vec_extension


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def build_engine(db_name: str):
    """Create an async SQLite engine for the given database name."""
    config.DATABASES_DIR.mkdir(parents=True, exist_ok=True)
    db_path: Path = config.DATABASES_DIR / f'{db_name}.sqlite3'
    engine = create_async_engine(f'sqlite+aiosqlite:///{db_path}')
    register_vec_extension(engine)
    return engine


def build_sessionmaker(engine) -> async_sessionmaker[AsyncSession]:
    """Build an async session factory bound to the given engine."""
    return async_sessionmaker(engine, expire_on_commit=False)


async def init_db(engine) -> None:
    """Create all tables defined on Base.metadata if they do not exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await create_vec_table(conn)
