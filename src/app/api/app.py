from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core import OllamaClient
from app.core.chroma import build_chroma_client, get_app_collection
from app.core.db import build_engine, build_sessionmaker, init_db
from app.services import RAGService

from .routes import router


def create_app(db_name: str) -> FastAPI:
    """Build a FastAPI app wired to the given SQLite database."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = build_engine(db_name)
        session_factory = build_sessionmaker(engine)
        await init_db(engine)
        chroma_client = build_chroma_client(db_name)
        collection = get_app_collection(chroma_client)
        client = OllamaClient()
        app.state.rag_service = RAGService(session_factory, client, collection)
        try:
            yield
        finally:
            await client.aclose()
            await engine.dispose()

    app = FastAPI(title='get_apps RAG', lifespan=lifespan)
    app.include_router(router)
    return app
