from fastapi import APIRouter, Request

from app.core import config
from app.schemas import (
    OllamaStatusSchema,
    SystemStatusSchema,
)

router = APIRouter(tags=['system'])


@router.get('/status', response_model=SystemStatusSchema)
async def system_status(request: Request) -> SystemStatusSchema:
    """Aggregated backend + Ollama runtime status for the UI status indicator."""
    state = request.app.state.ollama_runtime.state
    return SystemStatusSchema(
        backend='ready',
        ollama=OllamaStatusSchema(
            status=state.status.value,
            detail=state.detail,
            model=config.OLLAMA_LLM_MODEL,
        ),
    )
