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
_VALID_INTENTS: frozenset[str] = frozenset({'smalltalk', 'app_query', 'other'})

_CATEGORY_PATTERNS: dict[str, re.Pattern[str]] = {
    'finance': re.compile(r'finance|финанс|банк|деньг'),
    'state': re.compile(r'state|госу|государ'),
    'tools': re.compile(r'tool|утилит|инструмент'),
    'transport': re.compile(r'transport|транспорт|навигац'),
    'purchases': re.compile(r'purchase|покуп|шоп|маркет'),
    'social': re.compile(r'social|социал|общени'),
    'entertainment': re.compile(r'entertain|развлеч'),
    'adsandservices': re.compile(r'\bads\b|объявлен|услуг|серви'),
    'business': re.compile(r'business|бизнес'),
    'health': re.compile(r'health|здоров|медиц'),
    'travelling': re.compile(r'travel|путеш|туриз'),
    'education': re.compile(r'educat|образован|обучен|учеб'),
    'books': re.compile(r'book|книг|чтени'),
    'lifestyle': re.compile(r'lifestyle|стиль жизн|образ жизн'),
    'sport': re.compile(r'sport|спорт|фитнес'),
    'news': re.compile(r'news|новост'),
    'parenting': re.compile(r'parent|родител|для детей|детск'),
    'pets': re.compile(r'\bpet\b|pets|питом|животн'),
    'gambling': re.compile(r'gambl|азарт|казино|ставк'),
    'foodanddrink': re.compile(r'food|drink|\bеда\b|готов|рестора|кухн|напит'),
}

_ANALYZE_SYSTEM_PROMPT = (
    'You analyze a user query about mobile apps. '
    'Return ONLY one JSON object — no prose, no markdown.\n'
    '\n'
    'Required fields:\n'
    '- intent: one of "smalltalk" (greetings, chit-chat, meta questions about you), '
    '"app_query" (asking for apps or app ideas), "other".\n'
    '- language: ISO-639-1 code of the user query language ("ru", "en", ...).\n'
    '- search_query: a 2–3 sentence catalog-style description of an ideal app that would '
    'satisfy the query, written in the SAME language as the query. Empty string for non-app queries.\n'
    '- smalltalk_reply: a one-sentence reply in the same language as the query, ONLY when '
    'intent="smalltalk". Empty string otherwise.\n'
    '- filters: object with optional fields, include each ONLY if the user explicitly mentioned it:\n'
    '    min_downloads, max_downloads (int), min_rating (number 0..5),\n'
    '    categories_any (array, lowercase, ONLY values from the closed list below),\n'
    '    above_median_downloads (bool, true ONLY if user said "popular"/"trending"/"above median"),\n'
    '    requested_count (int 1..50, only if user explicitly named a number).\n'
    '  Never invent values. For general queries return "filters": {}.\n'
    '\n'
    f'Allowed category values: {", ".join(config.RUSTORE_CATEGORIES)}.\n'
    'Any other category — including movie genres — is forbidden. If the user names a category '
    'that is not in the list, omit categories_any entirely.\n'
    '\n'
    'Examples:\n'
    'Query: "Привет"\n'
    '{"intent":"smalltalk","language":"ru","search_query":"",'
    '"smalltalk_reply":"Привет! Чем могу помочь?","filters":{}}\n'
    '\n'
    'Query: "Предложи 3 идеи приложений которые будут работать без интернета"\n'
    '{"intent":"app_query","language":"ru",'
    '"search_query":"Мобильные приложения, работающие полностью офлайн без подключения к интернету: '
    'утилиты, игры и инструменты, не требующие сети.",'
    '"smalltalk_reply":"","filters":{"requested_count":3}}\n'
    '\n'
    'Query: "Финансовые приложения с рейтингом 4+"\n'
    '{"intent":"app_query","language":"ru",'
    '"search_query":"Личные финансы: бюджет, банкинг, инвестиции, учёт расходов.",'
    '"smalltalk_reply":"","filters":{"categories_any":["finance"],"min_rating":4}}\n'
)

_ANSWER_SYSTEM_PROMPT = (
    'You help users find app ideas from a provided catalog. '
    'Ground your answer ONLY in the apps listed in the context and reference them by their numbers [N]. '
    'If the context is empty or has no relevant matches, say so plainly in the requested language. '
    'Never invent apps that are not in the context.'
)


@dataclass
class QueryAnalysis:
    """Output of the analyze stage: intent, language, HyDE search query, filters, smalltalk reply."""

    intent: str
    language: str
    search_query: str
    filters: FilterSpec
    smalltalk_reply: str


@dataclass
class RAGResponse:
    """Final answer from the RAG pipeline with the sources used."""

    answer: str
    filters: FilterSpec
    sources: list[RetrievedApp]


class RAGService:
    """Orchestrate analysis (intent + language + HyDE + filters), retrieval, and answer generation."""

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
        analysis = await self._analyze(query)
        logger.info(
            'analyze: intent=%s language=%s filters=%s search_query=%r',
            analysis.intent,
            analysis.language,
            analysis.filters,
            analysis.search_query[:120],
        )
        if analysis.intent == 'smalltalk' and analysis.smalltalk_reply:
            return RAGResponse(
                answer=analysis.smalltalk_reply,
                filters=analysis.filters,
                sources=[],
            )
        effective_top_k = top_k or analysis.filters.requested_count
        retrieve_text = analysis.search_query or query
        sources = await self._retrieval.search(retrieve_text, analysis.filters, top_k=effective_top_k)
        answer_text = await self._generate_answer(query, analysis.language, sources)
        return RAGResponse(answer=answer_text, filters=analysis.filters, sources=sources)

    async def _analyze(self, query: str) -> QueryAnalysis:
        """Single LLM call producing intent, language, HyDE search query, filters, and an optional smalltalk reply."""
        try:
            raw = await self._client.generate(
                prompt=f'User query: {query}',
                system=_ANALYZE_SYSTEM_PROMPT,
                json_format=True,
            )
        except Exception:
            logger.exception('analyze failed; falling back to defaults')
            return _default_analysis(query)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning('analyze returned non-JSON: %r', raw[:200])
            return _default_analysis(query)
        if not isinstance(data, dict):
            return _default_analysis(query)
        return _coerce_analysis(query, data)

    async def _generate_answer(self, query: str, language: str, sources: list[RetrievedApp]) -> str:
        """Render the source context and call the LLM with a hard language pin."""
        context = self._format_context(sources) if sources else '(no apps matched the query)'
        lang_pin = (
            f'Reply strictly in language "{language}".'
            if language
            else 'Reply in the same language as the user query.'
        )
        prompt = (
            f'{lang_pin}\n\n'
            f'User query: {query}\n\n'
            f'Context (apps from the catalog):\n{context}\n\n'
            f'Provide a thorough answer in the requested language.'
        )
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


def _default_analysis(query: str) -> QueryAnalysis:
    """Safe fallback used when the analyze LLM call fails or returns malformed output."""
    return QueryAnalysis(
        intent='app_query',
        language='',
        search_query=query,
        filters=FilterSpec(),
        smalltalk_reply='',
    )


def _coerce_analysis(query: str, data: dict) -> QueryAnalysis:
    """Normalize the raw analyze JSON into a QueryAnalysis with safe defaults."""
    intent_raw = data.get('intent')
    intent = intent_raw if intent_raw in _VALID_INTENTS else 'app_query'

    language_raw = data.get('language')
    language = language_raw.strip().lower() if isinstance(language_raw, str) else ''

    search_query_raw = data.get('search_query')
    search_query = search_query_raw.strip() if isinstance(search_query_raw, str) else ''

    smalltalk_raw = data.get('smalltalk_reply')
    smalltalk_reply = smalltalk_raw.strip() if isinstance(smalltalk_raw, str) else ''

    filters_raw = data.get('filters')
    filters = _coerce_filter(query, filters_raw if isinstance(filters_raw, dict) else {})

    return QueryAnalysis(
        intent=intent,
        language=language,
        search_query=search_query,
        filters=filters,
        smalltalk_reply=smalltalk_reply,
    )


def _coerce_filter(query: str, data: dict) -> FilterSpec:
    """Coerce the filters JSON into a FilterSpec; reject categories the user did not actually mention."""
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
        whitelisted = [c for c in valid if c in _VALID_CATEGORIES]
        spec.categories_any = _sanitize_categories(query, whitelisted)
    if data.get('above_median_downloads') is True:
        spec.above_median_downloads = True
    requested_count = data.get('requested_count')
    if isinstance(requested_count, int) and 1 <= requested_count <= 50:
        spec.requested_count = requested_count
    return spec


def _sanitize_categories(query: str, categories: list[str]) -> list[str]:
    """Drop any category whose synonyms do not appear in the original query — defends against LLM hallucinations."""
    haystack = query.lower()
    kept: list[str] = []
    for cat in categories:
        pattern = _CATEGORY_PATTERNS.get(cat)
        if pattern is None:
            continue
        if pattern.search(haystack):
            kept.append(cat)
        else:
            logger.info('sanitize: dropped hallucinated category %r (not mentioned in query)', cat)
    return kept
