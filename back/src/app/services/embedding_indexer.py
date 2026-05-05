import asyncio
import json
import logging
import math
import re
import unicodedata

from chromadb.api.models.Collection import Collection
from sqlalchemy import bindparam, text

from app.core import TextEmbedder
from app.core.storage import (
    build_chroma_client,
    build_engine,
    build_sessionmaker,
    get_app_collection,
    init_db,
)

logger = logging.getLogger(__name__)

_DESCRIPTION_CHAR_LIMIT = 2000
_CHUNK_CHAR_LIMIT = 1000
_WHITESPACE_RE = re.compile(r'\s+')
_DROP_CATEGORIES = frozenset({'So', 'Sk', 'Cs', 'Cf', 'Co'})


def _clean_text(value: str) -> str:
    """NFKC-normalize, drop emoji/decorative symbols, collapse whitespace."""

    normalized = unicodedata.normalize('NFKC', value)
    filtered = ''.join(ch for ch in normalized if unicodedata.category(ch) not in _DROP_CATEGORIES)

    return _WHITESPACE_RE.sub(' ', filtered).strip()


class EmbeddingIndexerService:
    """Index app_info rows into a Chroma collection of embeddings."""

    def __init__(
        self,
        db_name: str,
        embedder: TextEmbedder,
        batch_size: int = 32,
        concurrency: int = 1,
    ) -> None:
        if concurrency < 1:
            raise ValueError('concurrency must be >= 1')
        self.db_name = db_name
        self.embedder = embedder
        self.batch_size = batch_size
        self.concurrency = concurrency

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

            batches = [pending[start : start + self.batch_size] for start in range(0, len(pending), self.batch_size)]
            semaphore = asyncio.Semaphore(self.concurrency)
            write_lock = asyncio.Lock()
            total = len(pending)
            done = 0

            async def process(batch: list[dict]) -> None:
                nonlocal done

                async with semaphore:
                    chunks_per_row = [_chunk_text(self._build_text(row)) for row in batch]
                    flat_texts = [c for chunks in chunks_per_row for c in chunks]
                    flat_vectors = await self.embedder.embed_passages(flat_texts)
                    ids = [row['app_id'] for row in batch]
                    vectors: list[list[float]] = []
                    offset = 0

                    for chunks in chunks_per_row:
                        n = len(chunks)
                        vectors.append(_average_unit(flat_vectors[offset : offset + n]))
                        offset += n

                async with write_lock:
                    await asyncio.to_thread(collection.add, ids=ids, embeddings=vectors)
                    done += len(batch)
                    logger.info('Indexed %d/%d', done, total)

            await asyncio.gather(*(process(b) for b in batches))
        finally:
            await engine.dispose()

    @staticmethod
    async def _load_pending(session_factory, indexed_ids: set[str]) -> list[dict]:
        """Return rows from app_info whose app_id is not yet in the Chroma collection.

        Two-step to avoid materializing description/categories for already-indexed rows:
        first fetch just the ids, then pull full rows for the pending subset in chunks
        to stay under SQLite's bound-parameter limit.
        """

        async with session_factory() as session:
            id_rows = await session.execute(text('SELECT app_id FROM app_info'))
            pending_ids = [row[0] for row in id_rows.all() if row[0] not in indexed_ids]

            if not pending_ids:
                return []

            chunk_size = 500
            select_sql = text(
                'SELECT app_id, name, description, categories FROM app_info WHERE app_id IN :ids'
            ).bindparams(bindparam('ids', expanding=True))
            rows: list[dict] = []

            for start in range(0, len(pending_ids), chunk_size):
                chunk = pending_ids[start : start + chunk_size]
                result = await session.execute(select_sql, {'ids': chunk})
                rows.extend(dict(row._mapping) for row in result.all())

            return rows

    @staticmethod
    def _build_text(row: dict) -> str:
        """Assemble the text to embed from name, categories and description.

        Empty/whitespace-only fields are ignored. Falls back to app_id so the
        input is never empty.
        """

        name = _clean_text(row.get('name') or '')
        description = _clean_text(row.get('description') or '')[:_DESCRIPTION_CHAR_LIMIT]
        categories_raw = row.get('categories')

        if isinstance(categories_raw, str):
            try:
                categories_raw = json.loads(categories_raw)
            except json.JSONDecodeError:
                pass

        if isinstance(categories_raw, list):
            categories = ', '.join(cleaned for c in categories_raw if (cleaned := _clean_text(str(c))))
        elif isinstance(categories_raw, str):
            categories = _clean_text(categories_raw)
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


def _chunk_text(text_value: str) -> list[str]:
    """Split text into pieces of at most _CHUNK_CHAR_LIMIT chars, preserving all content.

    Prefers paragraph, then sentence, then word boundaries; falls back to a hard cut
    only when no whitespace exists in the window. Short inputs are returned as-is.
    """

    if not text_value:
        return ['']
    if len(text_value) <= _CHUNK_CHAR_LIMIT:
        return [text_value]

    chunks: list[str] = []
    remaining = text_value

    while len(remaining) > _CHUNK_CHAR_LIMIT:
        cut = _find_cut(remaining, _CHUNK_CHAR_LIMIT)
        piece = remaining[:cut].strip()
        if piece:
            chunks.append(piece)
        remaining = remaining[cut:].lstrip()

    if remaining:
        chunks.append(remaining)

    return chunks or [text_value]


def _find_cut(text_value: str, limit: int) -> int:
    """Return best split index <= limit; prefers paragraph > sentence > word > hard cut."""

    window = text_value[:limit]
    min_cut = limit // 2

    for sep in ('\n\n', '. ', '.\n', '! ', '? ', '\n', ' '):
        idx = window.rfind(sep)
        if idx >= min_cut:
            return idx + len(sep)

    return limit


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
