import json
import logging
from dataclasses import dataclass, field

from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import OllamaClient, config
from app.core.vec import serialize_vector

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
    """Hybrid retrieval: vec0 kNN + structural SQL filters over app_info."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession], client: OllamaClient) -> None:
        self._session_factory = session_factory
        self._client = client

    async def search(self, query_text: str, filters: FilterSpec, top_k: int | None = None) -> list[RetrievedApp]:
        """Embed the query, run filtered kNN, and return top_k retrieved apps."""
        top_k = top_k or config.RAG_TOP_K
        query_vector = await self._client.embed(query_text)

        async with self._session_factory() as session:
            median = await self._median_downloads(session) if filters.above_median_downloads else None
            rows = await self._search_with_filters(session, query_vector, filters, median, top_k)
        return [self._row_to_app(row) for row in rows]

    async def _search_with_filters(
        self,
        session: AsyncSession,
        query_vector: list[float],
        filters: FilterSpec,
        median: int | None,
        top_k: int,
    ) -> list[dict]:
        where: list[str] = []
        params: dict = {
            'query_vec': serialize_vector(query_vector),
            'candidate_k': config.RAG_CANDIDATE_K,
            'top_k': top_k,
        }

        if filters.min_downloads is not None:
            where.append('ai.downloads >= :min_downloads')
            params['min_downloads'] = filters.min_downloads
        if filters.max_downloads is not None:
            where.append('ai.downloads <= :max_downloads')
            params['max_downloads'] = filters.max_downloads
        if filters.min_rating is not None:
            where.append('ai.rating >= :min_rating')
            params['min_rating'] = filters.min_rating
        if median is not None:
            where.append('ai.downloads > :median_downloads')
            params['median_downloads'] = median
        if filters.categories_any:
            where.append(
                'EXISTS (SELECT 1 FROM json_each(ai.categories) je WHERE je.value IN :categories_any)'
            )
            params['categories_any'] = filters.categories_any

        filter_sql = ' AND '.join(where)
        if filter_sql:
            filter_sql = ' AND ' + filter_sql

        sql = text(
            'SELECT ae.app_id AS app_id, ae.distance AS distance, '
            'ai.name AS name, ai.description AS description, '
            'ai.rating AS rating, ai.downloads AS downloads, '
            'ai.categories AS categories, ai.url AS url '
            'FROM app_embeddings ae '
            'JOIN app_info ai ON ai.app_id = ae.app_id '
            'WHERE ae.embedding MATCH :query_vec AND ae.k = :candidate_k'
            f'{filter_sql} '
            'ORDER BY ae.distance '
            'LIMIT :top_k'
        )
        if filters.categories_any:
            sql = sql.bindparams(bindparam('categories_any', expanding=True))

        result = await session.execute(sql, params)
        return [dict(row._mapping) for row in result.all()]

    @staticmethod
    async def _median_downloads(session: AsyncSession) -> int:
        """Compute the median of non-null downloads in app_info."""
        result = await session.execute(
            text('SELECT downloads FROM app_info WHERE downloads IS NOT NULL ORDER BY downloads')
        )
        values = [row[0] for row in result.all()]
        if not values:
            return 0
        n = len(values)
        mid = n // 2
        if n % 2:
            return int(values[mid])
        return int((values[mid - 1] + values[mid]) // 2)

    @staticmethod
    def _row_to_app(row: dict) -> RetrievedApp:
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
            distance=float(row.get('distance') or 0.0),
        )
