from fastapi import Request

from app.core import TextEmbedder
from app.core.jobs import JobManager


def get_jobs(request: Request) -> JobManager:
    """Job manager created in the app lifespan."""
    return request.app.state.jobs


def get_embedder(request: Request) -> TextEmbedder:
    """Shared embedder created in the app lifespan."""
    return request.app.state.embedder
