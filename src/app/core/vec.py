import sqlite_vec
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine
from sqlalchemy.util.concurrency import await_only

from .config import config


def register_vec_extension(engine: AsyncEngine) -> None:
    """Load the sqlite-vec extension on every new DBAPI connection."""

    @event.listens_for(engine.sync_engine, 'connect')
    def _load(dbapi_connection, _):
        driver = dbapi_connection.driver_connection
        await_only(driver.enable_load_extension(True))
        await_only(driver.load_extension(sqlite_vec.loadable_path()))
        await_only(driver.enable_load_extension(False))


async def create_vec_table(conn: AsyncConnection) -> None:
    """Create the vec0 virtual table for app embeddings if it doesn't exist."""
    dim = config.EMBEDDING_DIM
    await conn.exec_driver_sql(
        f'CREATE VIRTUAL TABLE IF NOT EXISTS app_embeddings USING vec0('
        f'app_id TEXT PRIMARY KEY, embedding FLOAT[{dim}])'
    )


def serialize_vector(values: list[float]) -> bytes:
    """Serialize a float32 vector into the layout expected by sqlite-vec."""
    return sqlite_vec.serialize_float32(values)
