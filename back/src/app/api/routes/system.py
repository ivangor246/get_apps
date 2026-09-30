from fastapi import APIRouter, Request

from app.core.config import get_config

from ..deps import get_embedder
from ..schemas.system import EmbeddingStatusSchema, OllamaStatusSchema, SystemStatusSchema

router = APIRouter()


@router.get('/health')
async def health() -> dict:
    """Liveness probe."""
    return {'status': 'ok'}


@router.get('/status', response_model=SystemStatusSchema)
async def system_status(request: Request) -> SystemStatusSchema:
    """Aggregated backend + Ollama runtime + embedding model status for the UI status indicator."""
    state = request.app.state.ollama_runtime.state
    embedder = get_embedder(request)
    if embedder.downloading:
        embedding_status = 'downloading'
    elif embedder.ready:
        embedding_status = 'ready'
    else:
        embedding_status = 'missing'
    return SystemStatusSchema(
        backend='ready',
        ollama=OllamaStatusSchema(
            status=state.status.value,
            detail=state.detail,
            model=get_config().OLLAMA_LLM_MODEL,
        ),
        embedding=EmbeddingStatusSchema(
            status=embedding_status,
            detail=embedder.error if embedding_status == 'missing' else None,
            model=embedder.model_name,
        ),
    )
