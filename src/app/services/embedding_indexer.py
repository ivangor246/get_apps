import asyncio
import json
import logging
import math

from chromadb.api.models.Collection import Collection
from sqlalchemy import text

from app.core import OllamaClient
from app.core.chroma import build_chroma_client, get_app_collection
from app.core.db import build_engine, build_sessionmaker, init_db

logger = logging.getLogger(__name__)

_DESCRIPTION_CHAR_LIMIT = 2000
_MIN_CHUNK_CHARS = 2


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
                        logger.warning(
                            'Embedding batch failed at offset %d, falling back to per-item', start
                        )
                        ids, vectors = await self._embed_individually(client, batch, texts)
                    else:
                        ids = [row['app_id'] for row in batch]
                    if ids:
                        await asyncio.to_thread(collection.add, ids=ids, embeddings=vectors)
                    logger.info('Indexed %d/%d', min(start + self.batch_size, len(pending)), len(pending))
        finally:
            await engine.dispose()

    @classmethod
    async def _embed_individually(
        cls, client: OllamaClient, batch: list[dict], texts: list[str]
    ) -> tuple[list[str], list[list[float]]]:
        """Retry a failed batch one text at a time, splitting NaN-producing inputs."""
        ids: list[str] = []
        vectors: list[list[float]] = []
        for row, text_value in zip(batch, texts, strict=True):
            try:
                vector = await cls._embed_with_split(client, text_value)
            except Exception:
                logger.exception('Embedding failed for app_id=%s', row['app_id'])
                continue
            ids.append(row['app_id'])
            vectors.append(vector)
        return ids, vectors

    @classmethod
    async def _embed_with_split(cls, client: OllamaClient, text_value: str) -> list[float]:
        """Embed text; on failure, split in half at whitespace and average the halves.

        Works around a bge-m3/Ollama numerical bug that returns NaN for certain
        token sequences. Recursion guarantees every non-empty fragment of the
        original text contributes to the final vector.
        """
        try:
            return await client.embed(text_value)
        except Exception:
            if len(text_value) <= _MIN_CHUNK_CHARS:
                raise
        mid = len(text_value) // 2
        cut = text_value.rfind(' ', 0, mid)
        if cut <= 0:
            cut = text_value.find(' ', mid)
        if cut <= 0:
            cut = mid
        left = text_value[:cut].strip()
        right = text_value[cut:].strip()
        pieces = [p for p in (left, right) if p]
        if not pieces:
            raise RuntimeError('Cannot split text further')
        vectors = [await cls._embed_with_split(client, p) for p in pieces]
        return _average_unit(vectors)

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
        """Assemble the text to embed from name, categories and description.

        Empty/whitespace-only fields are ignored. Falls back to app_id so the
        input is never empty (Ollama returns NaN embeddings for blank input).
        """
        name = (row.get('name') or '').strip()
        description = (row.get('description') or '').strip()[:_DESCRIPTION_CHAR_LIMIT]
        categories_raw = row.get('categories')
        if isinstance(categories_raw, str):
            try:
                categories_raw = json.loads(categories_raw)
            except json.JSONDecodeError:
                pass
        if isinstance(categories_raw, list):
            categories = ', '.join(str(c).strip() for c in categories_raw if str(c).strip())
        elif isinstance(categories_raw, str):
            categories = categories_raw.strip()
        else:
            categories = ''
        parts: list[str] = []
        if name:
            parts.append(name)
        if categories:
            parts.append(f'Категории: {categories}')
        if description:
            parts.append(description)
        if not parts:
            parts.append(str(row.get('app_id') or ''))
        return '\n\n'.join(parts)


def _load_indexed_ids(collection: Collection) -> set[str]:
    """Return the set of app_ids currently stored in the Chroma collection."""
    data = collection.get(include=[])
    return set(data.get('ids') or [])


def _average_unit(vectors: list[list[float]]) -> list[float]:
    """Mean-pool embeddings and L2-normalize so the result is a unit vector."""
    if len(vectors) == 1:
        return vectors[0]
    dim = len(vectors[0])
    n = len(vectors)
    avg = [sum(v[i] for v in vectors) / n for i in range(dim)]
    norm = math.sqrt(sum(x * x for x in avg))
    if norm == 0:
        return avg
    return [x / norm for x in avg]
