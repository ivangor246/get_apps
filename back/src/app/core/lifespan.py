import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from app.core import OllamaClient, TextEmbedder
from app.core.storage import (
    build_chroma_client,
    build_engine,
    build_sessionmaker,
    get_app_collection,
    init_db,
)
from app.core.jobs import JobManager
from app.core.ollama import OllamaRuntime
from app.services import RAGService


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = OllamaClient()
    ollama_runtime = OllamaRuntime(client)
    startup_task = asyncio.create_task(ollama_runtime.start())
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
    app.state.ollama_runtime = ollama_runtime
    app.state.embedder = embedder
    app.state.get_rag_service = get_rag_service
    try:
        yield
    finally:
        startup_task.cancel()
        with suppress(asyncio.CancelledError):
            await startup_task
        await ollama_runtime.stop()
        await client.aclose()
        for engine in engines.values():
            await engine.dispose()
