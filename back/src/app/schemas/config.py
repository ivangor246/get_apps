from pydantic import BaseModel


class TunableConfigSchema(BaseModel):
    """Config values that can be overridden per-request via query parameters."""

    OLLAMA_LLM_MODEL: str
    OLLAMA_TIMEOUT: float
    OLLAMA_CONTEXT_SIZE: int
    RAG_TOP_K: int
    RAG_CANDIDATE_K: int
    EMBEDDING_BATCH_SIZE: int


class ReadOnlyConfigSchema(BaseModel):
    """Config values fixed at backend startup; require code edit and restart to change."""

    OLLAMA_URL: str
    EMBEDDING_MODEL: str
    EMBEDDING_DIM: int


class ConfigSchema(BaseModel):
    """Backend-owned defaults split into tunable and read-only groups."""

    tunable: TunableConfigSchema
    read_only: ReadOnlyConfigSchema
