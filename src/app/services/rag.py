import json
import logging
import re
from dataclasses import dataclass

from chromadb.api.models.Collection import Collection
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import OllamaClient, TextEmbedder
from app.core.config import config

from .retrieval import FilterSpec, RetrievalService, RetrievedApp

logger = logging.getLogger(__name__)

_VALID_CATEGORIES: frozenset[str] = frozenset(config.RUSTORE_CATEGORIES)
_CYRILLIC_RE = re.compile(r'[а-яА-ЯёЁ]')

_FILTER_SYSTEM_PROMPT = (
    'You extract structural filters from a user query about mobile apps. '
    'Return ONLY a single JSON object — no prose, no markdown.\n'
    '\n'
    'CRITICAL RULE: include a field ONLY if the user explicitly mentioned it '
    '(named a number, a rating, a category, or used words like "popular" / "above median"). '
    'For general queries (greetings, "suggest some apps", "give me ideas") return an empty object {}. '
    'Never invent values. Never guess.\n'
    '\n'
    'Possible fields (all optional):\n'
    '- min_downloads (int): explicit minimum downloads\n'
    '- max_downloads (int): explicit maximum downloads\n'
    '- min_rating (number 0..5): explicit minimum rating\n'
    '- categories_any (array of strings): categories — ONLY from the closed list below, lowercase\n'
    '- above_median_downloads (bool): true ONLY if the user said "popular", "above median", '
    '"trending", or similar\n'
    '- requested_count (int 1..50): the number of apps the user explicitly asked for '
    '(e.g. "suggest 3 ideas", "list 5 apps")\n'
    '\n'
    f'Allowed categories_any values (use ONLY these): {", ".join(config.RUSTORE_CATEGORIES)}\n'
    'Any other category — including movie genres (action, comedy, fantasy, etc.) — is forbidden. '
    'If the user names a category that is not in the list, omit categories_any entirely.\n'
    '\n'
    'Examples:\n'
    'Query: "Suggest 3 app ideas" -> {"requested_count": 3}\n'
    'Query: "Предложи 3 идеи приложений" -> {"requested_count": 3}\n'
    'Query: "Suggest some apps" -> {}\n'
    'Query: "Hi" -> {}\n'
    'Query: "Привет" -> {}\n'
    'Query: "Финансовые приложения с рейтингом 4+" -> '
    '{"categories_any": ["finance"], "min_rating": 4}\n'
    'Query: "Popular health apps" -> {"categories_any": ["health"], "above_median_downloads": true}\n'
    'Query: "Apps with more than 100000 downloads" -> {"min_downloads": 100000}\n'
)

_ANSWER_SYSTEM_PROMPT = (
    'You help users find app ideas from the provided catalog. '
    'Reply in the same language as the user query; if the language is unclear, reply in English. '
    'Ground your answer ONLY in the apps listed in the context and reference them by their numbers [N]. '
    'If the context is empty or has no relevant matches, say so plainly.'
)

_NO_MATCHES_EN = 'No apps in the catalog match the query under the applied filters.'
_NO_MATCHES_RU = 'По базе не нашлось приложений, подходящих под запрос с учётом фильтров.'


@dataclass
class RAGResponse:
    """Final answer from the RAG pipeline with the sources used."""

    answer: str
    filters: FilterSpec
    sources: list[RetrievedApp]


class RAGService:
    """Orchestrate filter extraction, retrieval, and answer generation."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        client: OllamaClient,
        embedder: TextEmbedder,
        collection: Collection,
    ) -> None:
        self._client = client
        self._retrieval = RetrievalService(session_factory, embedder, collection)

    async def answer(self, query: str, top_k: int | None = None) -> RAGResponse:
        """Run the full RAG pipeline for a user query."""
        filters = await self._extract_filters(query)
        effective_top_k = top_k or filters.requested_count
        sources = await self._retrieval.search(query, filters, top_k=effective_top_k)
        answer_text = await self._generate_answer(query, sources)
        return RAGResponse(answer=answer_text, filters=filters, sources=sources)

    async def _extract_filters(self, query: str) -> FilterSpec:
        """Call the LLM to extract a FilterSpec JSON from the user query."""
        try:
            raw = await self._client.generate(
                prompt=f'Запрос пользователя: {query}',
                system=_FILTER_SYSTEM_PROMPT,
                json_format=True,
            )
        except Exception:
            logger.exception('Filter extraction failed; falling back to empty filter')
            return FilterSpec()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning('LLM returned non-JSON filter payload: %r', raw[:200])
            return FilterSpec()
        if not isinstance(data, dict):
            return FilterSpec()
        return self._coerce_filter(data)

    @staticmethod
    def _coerce_filter(data: dict) -> FilterSpec:
        """Coerce the parsed JSON into a FilterSpec, ignoring malformed or hallucinated fields."""
        spec = FilterSpec()
        min_downloads = data.get('min_downloads')
        if isinstance(min_downloads, (int, float)):
            spec.min_downloads = int(min_downloads)
        max_downloads = data.get('max_downloads')
        if isinstance(max_downloads, (int, float)):
            spec.max_downloads = int(max_downloads)
        min_rating = data.get('min_rating')
        if isinstance(min_rating, (int, float)):
            spec.min_rating = float(min_rating)
        categories = data.get('categories_any')
        if isinstance(categories, list):
            valid = [str(c).lower() for c in categories if isinstance(c, str)]
            spec.categories_any = [c for c in valid if c in _VALID_CATEGORIES]
        if data.get('above_median_downloads') is True:
            spec.above_median_downloads = True
        requested_count = data.get('requested_count')
        if isinstance(requested_count, int) and 1 <= requested_count <= 50:
            spec.requested_count = requested_count
        return spec

    async def _generate_answer(self, query: str, sources: list[RetrievedApp]) -> str:
        """Render a context block from sources and call the LLM for the final answer."""
        if not sources:
            return _NO_MATCHES_RU if _CYRILLIC_RE.search(query) else _NO_MATCHES_EN
        context = self._format_context(sources)
        prompt = f'Query: {query}\n\nContext (apps from the catalog):\n{context}\n\nProvide a thorough answer.'
        return await self._client.generate(prompt=prompt, system=_ANSWER_SYSTEM_PROMPT)

    @staticmethod
    def _format_context(sources: list[RetrievedApp]) -> str:
        blocks: list[str] = []
        for idx, app in enumerate(sources, start=1):
            header = f'[{idx}] {app.name or app.app_id}'
            meta_parts: list[str] = []
            if app.downloads is not None:
                meta_parts.append(f'скачиваний: {app.downloads}')
            if app.rating is not None:
                meta_parts.append(f'рейтинг: {app.rating}')
            if app.categories:
                meta_parts.append(f'категории: {", ".join(app.categories)}')
            meta = ' | '.join(meta_parts)
            description = (app.description or '').strip().replace('\n', ' ')[:500]
            blocks.append(f'{header}\n{meta}\nОписание: {description}')
        return '\n\n'.join(blocks)
