from pydantic import BaseModel


class AppConfig(BaseModel):
    """Tunable runtime settings; mirrors Config dataclass fields."""

    OLLAMA_URL: str
    OLLAMA_LLM_MODEL: str
    OLLAMA_TIMEOUT: float
    OLLAMA_CONTEXT_SIZE: int
    EMBEDDING_MODEL: str
    EMBEDDING_DEVICE: str
    EMBEDDING_DIM: int
    EMBEDDING_BATCH_SIZE: int
    EMBEDDING_GPU_MEM_LIMIT_MB: int
    RAG_TOP_K: int
    RAG_CANDIDATE_K: int
    API_HOST: str
    API_PORT: int


class AppConfigPatch(BaseModel):
    """Partial update for AppConfig; every field optional."""

    OLLAMA_URL: str | None = None
    OLLAMA_LLM_MODEL: str | None = None
    OLLAMA_TIMEOUT: float | None = None
    OLLAMA_CONTEXT_SIZE: int | None = None
    EMBEDDING_MODEL: str | None = None
    EMBEDDING_DEVICE: str | None = None
    EMBEDDING_DIM: int | None = None
    EMBEDDING_BATCH_SIZE: int | None = None
    EMBEDDING_GPU_MEM_LIMIT_MB: int | None = None
    RAG_TOP_K: int | None = None
    RAG_CANDIDATE_K: int | None = None
    API_HOST: str | None = None
    API_PORT: int | None = None
