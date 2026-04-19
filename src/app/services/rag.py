import json
import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import OllamaClient

from .retrieval import FilterSpec, RetrievalService, RetrievedApp

logger = logging.getLogger(__name__)

_FILTER_SYSTEM_PROMPT = (
    'Ты извлекаешь структурные фильтры из пользовательского запроса о приложениях. '
    'Верни строго JSON-объект со следующими ключами (любой из них можно опустить или оставить null):\n'
    '- min_downloads (целое): минимальное количество скачиваний\n'
    '- max_downloads (целое): максимальное количество скачиваний\n'
    '- min_rating (число от 0 до 5): минимальный рейтинг\n'
    '- categories_any (массив строк): названия категорий, если пользователь их перечислил\n'
    '- above_median_downloads (bool): true, если пользователь просит приложения с количеством '
    'скачиваний выше медианного по базе\n'
    'Никакого текста вне JSON. Если фильтр не упомянут — не включай его в ответ.'
)

_ANSWER_SYSTEM_PROMPT = (
    'Ты помогаешь искать идеи приложений по предоставленному каталогу. '
    'Отвечай на русском, опирайся только на приложения из контекста, ссылайся на них номерами [N]. '
    'Если в контексте нет подходящих примеров — скажи об этом прямо.'
)


@dataclass
class RAGResponse:
    """Final answer from the RAG pipeline with the sources used."""

    answer: str
    filters: FilterSpec
    sources: list[RetrievedApp]


class RAGService:
    """Orchestrate filter extraction, retrieval, and answer generation."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession], client: OllamaClient) -> None:
        self._client = client
        self._retrieval = RetrievalService(session_factory, client)

    async def answer(self, query: str, top_k: int | None = None) -> RAGResponse:
        """Run the full RAG pipeline for a user query."""
        filters = await self._extract_filters(query)
        sources = await self._retrieval.search(query, filters, top_k=top_k)
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
        """Coerce the parsed JSON into a FilterSpec, ignoring malformed fields."""
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
            spec.categories_any = [str(c) for c in categories if c]
        if data.get('above_median_downloads') is True:
            spec.above_median_downloads = True
        return spec

    async def _generate_answer(self, query: str, sources: list[RetrievedApp]) -> str:
        """Render a context block from sources and call the LLM for the final answer."""
        if not sources:
            return 'По базе не нашлось приложений, подходящих под запрос с учётом фильтров.'
        context = self._format_context(sources)
        prompt = f'Запрос: {query}\n\nКонтекст (приложения из базы):\n{context}\n\nДай развёрнутый ответ.'
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
