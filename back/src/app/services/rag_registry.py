import asyncio

from sqlalchemy.ext.asyncio import AsyncEngine

from app.core import OllamaClient, TextEmbedder
from app.core.storage import (
    build_chroma_client,
    build_engine,
    build_sessionmaker,
    get_app_collection,
    init_db,
)

from .rag import RAGService


class RAGRegistry:
    """Per-DB cache of RAGService instances; lazily builds engine + Chroma client on first use."""

    def __init__(self, client: OllamaClient, embedder: TextEmbedder) -> None:
        self._client = client
        self._embedder = embedder
        self._services: dict[str, RAGService] = {}
        self._engines: dict[str, AsyncEngine] = {}
        self._lock = asyncio.Lock()

    async def get(self, db_name: str) -> RAGService:
        """Return the cached RAGService for db_name, building it (and its engine) on miss."""

        if db_name in self._services:
            return self._services[db_name]

        async with self._lock:
            if db_name in self._services:
                return self._services[db_name]

            engine = build_engine(db_name)
            session_factory = build_sessionmaker(engine)
            await init_db(engine)

            chroma_client = build_chroma_client(db_name)
            collection = get_app_collection(chroma_client)
            self._services[db_name] = RAGService(session_factory, self._client, self._embedder, collection)
            self._engines[db_name] = engine

            return self._services[db_name]

    async def dispose(self) -> None:
        """Dispose every engine created by the registry."""

        for engine in self._engines.values():
            await engine.dispose()
        self._engines.clear()
        self._services.clear()
