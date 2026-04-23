import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import OllamaClient, TextEmbedder
from app.core.chroma import build_chroma_client, get_app_collection
from app.core.db import build_engine, build_sessionmaker, init_db
from app.core.jobs import JobManager
from app.services import RAGService

from .routes import router


def create_app() -> FastAPI:
    """Build the FastAPI app; RAG services are created lazily per db_name at request time."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        client = OllamaClient()
        embedder = TextEmbedder()
        rag_cache: dict[str, RAGService] = {}
        engines: dict[str, object] = {}
        lock = asyncio.Lock()

        async def get_rag_service(db_name: str) -> RAGService:
            if db_name in rag_cache:
                return rag_cache[db_name]
            async with lock:
                if db_name in rag_cache:
                    return rag_cache[db_name]
                engine = build_engine(db_name)
                session_factory = build_sessionmaker(engine)
                await init_db(engine)
                chroma_client = build_chroma_client(db_name)
                collection = get_app_collection(chroma_client)
                rag_cache[db_name] = RAGService(session_factory, client, embedder, collection)
                engines[db_name] = engine
                return rag_cache[db_name]

        app.state.jobs = JobManager()
        app.state.ollama = client
        app.state.embedder = embedder
        app.state.get_rag_service = get_rag_service
        try:
            yield
        finally:
            await client.aclose()
            for engine in engines.values():
                await engine.dispose()

    app = FastAPI(title='get_apps', lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_methods=['*'],
        allow_headers=['*'],
    )
    app.include_router(router)
    return app
