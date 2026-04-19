import asyncio
import json
import logging

from chromadb.api.models.Collection import Collection
from sqlalchemy import text

from app.core import OllamaClient
from app.core.chroma import build_chroma_client, get_app_collection
from app.core.db import build_engine, build_sessionmaker, init_db

logger = logging.getLogger(__name__)

_DESCRIPTION_CHAR_LIMIT = 2000


class EmbeddingIndexerService:
    """Index app_info rows into a Chroma collection of embeddings."""

    def __init__(self, db_name: str, batch_size: int = 32) -> None:
        self.db_name = db_name
        self.batch_size = batch_size

    async def run(self) -> None:
        """Embed every app that doesn't yet have a stored vector in Chroma."""
        engine = build_engine(self.db_name)
        session_factory = build_sessionmaker(engine)
        await init_db(engine)

        chroma_client = build_chroma_client(self.db_name)
        collection = get_app_collection(chroma_client)

        try:
            indexed_ids = await asyncio.to_thread(_load_indexed_ids, collection)
            pending = await self._load_pending(session_factory, indexed_ids)
            logger.info('Apps pending embedding: %d (already indexed: %d)', len(pending), len(indexed_ids))
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
                    await asyncio.to_thread(
                        collection.add,
                        ids=[row['app_id'] for row in batch],
                        embeddings=vectors,
                    )
                    logger.info('Indexed %d/%d', min(start + self.batch_size, len(pending)), len(pending))
        finally:
            await engine.dispose()

    @staticmethod
    async def _load_pending(session_factory, indexed_ids: set[str]) -> list[dict]:
        """Return rows from app_info that are not yet in the Chroma collection."""
        query = text('SELECT app_id, name, description, categories FROM app_info')
        async with session_factory() as session:
            result = await session.execute(query)
            return [
                dict(row._mapping)
                for row in result.all()
                if row._mapping['app_id'] not in indexed_ids
            ]

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


def _load_indexed_ids(collection: Collection) -> set[str]:
    """Return the set of app_ids currently stored in the Chroma collection."""
    data = collection.get(include=[])
    return set(data.get('ids') or [])
