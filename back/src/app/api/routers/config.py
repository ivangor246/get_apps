from fastapi import APIRouter

from app.core import config
from app.schemas import (
    ConfigSchema,
    ReadOnlyConfigSchema,
    TunableConfigSchema,
)

router = APIRouter(tags=['config'])


@router.get('/config', response_model=ConfigSchema)
async def get_config() -> ConfigSchema:
    """Expose backend-owned defaults so the frontend can seed its Settings UI."""
    return ConfigSchema(
        tunable=TunableConfigSchema(
            OLLAMA_TIMEOUT=config.OLLAMA_TIMEOUT,
            OLLAMA_CONTEXT_SIZE=config.OLLAMA_CONTEXT_SIZE,
            RAG_TOP_K=config.RAG_TOP_K,
            RAG_CANDIDATE_K=config.RAG_CANDIDATE_K,
            EMBEDDING_BATCH_SIZE=config.EMBEDDING_BATCH_SIZE,
        ),
        read_only=ReadOnlyConfigSchema(
            OLLAMA_URL=config.OLLAMA_URL,
            EMBEDDING_MODEL=config.EMBEDDING_MODEL,
            EMBEDDING_DIM=config.EMBEDDING_DIM,
        ),
    )
