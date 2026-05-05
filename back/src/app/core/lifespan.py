import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from app.core import OllamaClient, TextEmbedder
from app.core.jobs import JobManager
from app.core.ollama import OllamaRuntime
from app.services import RAGRegistry


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Build shared singletons, expose them on app.state, and tear them down on shutdown."""

    client = OllamaClient()
    ollama_runtime = OllamaRuntime(client)
    startup_task = asyncio.create_task(ollama_runtime.start())
    embedder = TextEmbedder()
    rag_registry = RAGRegistry(client, embedder)

    app.state.jobs = JobManager()
    app.state.ollama = client
    app.state.ollama_runtime = ollama_runtime
    app.state.embedder = embedder
    app.state.get_rag_service = rag_registry.get

    try:
        yield
    finally:
        startup_task.cancel()
        with suppress(asyncio.CancelledError):
            await startup_task
        await ollama_runtime.stop()
        await client.aclose()
        await rag_registry.dispose()
