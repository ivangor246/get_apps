import asyncio
import json
import logging
from dataclasses import dataclass, field

from chromadb.api.models.Collection import Collection
from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import OllamaClient, config

logger = logging.getLogger(__name__)


@dataclass
class FilterSpec:
    """Structured filter extracted from a user query."""

    min_downloads: int | None = None
    max_downloads: int | None = None
    min_rating: float | None = None
    categories_any: list[str] = field(default_factory=list)
    above_median_downloads: bool = False


@dataclass
class RetrievedApp:
    """One result from the retrieval service."""

    app_id: str
    name: str | None
    description: str | None
    rating: float | None
    downloads: int | None
    categories: list[str]
    url: str
    distance: float


class RetrievalService:
    """Hybrid retrieval: Chroma kNN + structural SQL filters over app_info."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        client: OllamaClient,
        collection: Collection,
    ) -> None:
        self._session_factory = session_factory
        self._client = client
        self._collection = collection

    async def search(self, query_text: str, filters: FilterSpec, top_k: int | None = None) -> list[RetrievedApp]:
        """Embed the query, run oversampled kNN in Chroma, filter via SQL, return top_k."""
        top_k = top_k or config.RAG_TOP_K
        query_vector = await self._client.embed(query_text)

        knn = await asyncio.to_thread(
            self._collection.query,
            query_embeddings=[query_vector],
            n_results=config.RAG_CANDIDATE_K,
        )
        candidate_ids: list[str] = knn['ids'][0] if knn.get('ids') else []
        distances: list[float] = knn['distances'][0] if knn.get('distances') else []
        if not candidate_ids:
            return []
        distance_map = dict(zip(candidate_ids, distances, strict=True))

        async with self._session_factory() as session:
            median = await self._median_downloads(session) if filters.above_median_downloads else None
            rows = await self._filter_candidates(session, candidate_ids, filters, median)

        results = [self._row_to_app(row, distance_map[row['app_id']]) for row in rows if row['app_id'] in distance_map]
        results.sort(key=lambda app: app.distance)
        return results[:top_k]

    @staticmethod
    async def _filter_candidates(
        session: AsyncSession,
        candidate_ids: list[str],
        filters: FilterSpec,
        median: int | None,
    ) -> list[dict]:
        where: list[str] = ['app_id IN :candidate_ids']
        params: dict = {'candidate_ids': candidate_ids}

        if filters.min_downloads is not None:
            where.append('downloads >= :min_downloads')
            params['min_downloads'] = filters.min_downloads
        if filters.max_downloads is not None:
            where.append('downloads <= :max_downloads')
            params['max_downloads'] = filters.max_downloads
        if filters.min_rating is not None:
            where.append('rating >= :min_rating')
            params['min_rating'] = filters.min_rating
        if median is not None:
            where.append('downloads > :median_downloads')
            params['median_downloads'] = median
        if filters.categories_any:
            where.append('EXISTS (SELECT 1 FROM json_each(categories) je WHERE je.value IN :categories_any)')
            params['categories_any'] = filters.categories_any

        sql = text(
            'SELECT app_id, name, description, rating, downloads, categories, url '
            'FROM app_info '
            f'WHERE {" AND ".join(where)}'
        ).bindparams(bindparam('candidate_ids', expanding=True))
        if filters.categories_any:
            sql = sql.bindparams(bindparam('categories_any', expanding=True))

        result = await session.execute(sql, params)
        return [dict(row._mapping) for row in result.all()]

    @staticmethod
    async def _median_downloads(session: AsyncSession) -> int:
        """Compute the median of non-null downloads in app_info via window functions."""
        result = await session.execute(
            text(
                'WITH ordered AS ('
                ' SELECT downloads,'
                ' ROW_NUMBER() OVER (ORDER BY downloads) AS rn,'
                ' COUNT(*) OVER () AS cnt'
                ' FROM app_info WHERE downloads IS NOT NULL'
                ') '
                'SELECT AVG(downloads) FROM ordered '
                'WHERE rn IN ((cnt + 1) / 2, (cnt + 2) / 2)'
            )
        )
        value = result.scalar()
        return int(value) if value is not None else 0

    @staticmethod
    def _row_to_app(row: dict, distance: float) -> RetrievedApp:
        categories = row.get('categories')
        if isinstance(categories, str):
            try:
                categories = json.loads(categories)
            except json.JSONDecodeError:
                categories = []
        if not isinstance(categories, list):
            categories = []
        return RetrievedApp(
            app_id=row['app_id'],
            name=row.get('name'),
            description=row.get('description'),
            rating=row.get('rating'),
            downloads=row.get('downloads'),
            categories=[str(c) for c in categories],
            url=row.get('url') or '',
            distance=float(distance),
        )
