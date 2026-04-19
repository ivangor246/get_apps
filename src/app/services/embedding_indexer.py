import json
import logging

from sqlalchemy import text

from app.core import OllamaClient
from app.core.db import build_engine, build_sessionmaker, init_db
from app.core.vec import serialize_vector

logger = logging.getLogger(__name__)

_DESCRIPTION_CHAR_LIMIT = 2000


class EmbeddingIndexerService:
    """Index app_info rows into the sqlite-vec app_embeddings table."""

    def __init__(self, db_name: str, batch_size: int = 32) -> None:
        self.db_name = db_name
        self.batch_size = batch_size

    async def run(self) -> None:
        """Embed every app that doesn't yet have a stored vector."""
        engine = build_engine(self.db_name)
        session_factory = build_sessionmaker(engine)
        await init_db(engine)

        try:
            pending = await self._load_pending(session_factory)
            logger.info('Apps pending embedding: %d', len(pending))
            if not pending:
                return

            async with OllamaClient() as client:
                for start in range(0, len(pending), self.batch_size):
                    batch = pending[start : start + self.batch_size]
                    texts = [self._build_text(row) for row in batch]
                    try:
                        vectors = await client.embed_batch(texts)
                    except Exception:
                        logger.exception('Embedding batch failed at offset %d', start)
                        continue
                    await self._persist_batch(session_factory, batch, vectors)
                    logger.info('Indexed %d/%d', min(start + self.batch_size, len(pending)), len(pending))
        finally:
            await engine.dispose()

    @staticmethod
    async def _load_pending(session_factory) -> list[dict]:
        """Return rows from app_info that are missing an embedding."""
        query = text(
            'SELECT app_id, name, description, categories '
            'FROM app_info '
            'WHERE app_id NOT IN (SELECT app_id FROM app_embeddings)'
        )
        async with session_factory() as session:
            result = await session.execute(query)
            return [dict(row._mapping) for row in result.all()]

    @staticmethod
    async def _persist_batch(session_factory, rows: list[dict], vectors: list[list[float]]) -> None:
        """Insert one batch of (app_id, embedding) pairs in a single transaction."""
        async with session_factory() as session:
            for row, vector in zip(rows, vectors, strict=True):
                await session.execute(
                    text('INSERT INTO app_embeddings(app_id, embedding) VALUES (:app_id, :embedding)'),
                    {'app_id': row['app_id'], 'embedding': serialize_vector(vector)},
                )
            await session.commit()

    @staticmethod
    def _build_text(row: dict) -> str:
        """Assemble the text to embed from name, categories and description."""
        name = row.get('name') or ''
        description = (row.get('description') or '')[:_DESCRIPTION_CHAR_LIMIT]
        categories_raw = row.get('categories')
        if isinstance(categories_raw, str):
            try:
                categories_raw = json.loads(categories_raw)
            except json.JSONDecodeError:
                pass
        if isinstance(categories_raw, list):
            categories = ', '.join(str(c) for c in categories_raw)
        elif isinstance(categories_raw, str):
            categories = categories_raw
        else:
            categories = ''
        parts = [name]
        if categories:
            parts.append(f'Категории: {categories}')
        if description:
            parts.append(description)
        return '\n\n'.join(parts)
