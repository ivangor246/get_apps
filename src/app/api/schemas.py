from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    """Tunable runtime settings; mirrors Config dataclass fields."""

    OLLAMA_URL: str
    OLLAMA_LLM_MODEL: str
    OLLAMA_TIMEOUT: float
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
    EMBEDDING_MODEL: str | None = None
    EMBEDDING_DEVICE: str | None = None
    EMBEDDING_DIM: int | None = None
    EMBEDDING_BATCH_SIZE: int | None = None
    EMBEDDING_GPU_MEM_LIMIT_MB: int | None = None
    RAG_TOP_K: int | None = None
    RAG_CANDIDATE_K: int | None = None
    API_HOST: str | None = None
    API_PORT: int | None = None


class RAGQueryRequest(BaseModel):
    """Body for POST /rag/query."""

    query: str = Field(..., min_length=1, description='Natural-language user query.')
    top_k: int | None = Field(default=None, ge=1, le=100, description='Override for top_k retrieved apps.')


class SourceApp(BaseModel):
    """One app returned alongside a RAG answer."""

    app_id: str
    name: str | None = None
    url: str
    rating: float | None = None
    downloads: int | None = None
    categories: list[str] = []
    distance: float


class AppliedFilters(BaseModel):
    """Structural filters extracted from the query and applied during retrieval."""

    min_downloads: int | None = None
    max_downloads: int | None = None
    min_rating: float | None = None
    categories_any: list[str] = []
    above_median_downloads: bool = False


class RAGQueryResponse(BaseModel):
    """Response body for POST /rag/query."""

    answer: str
    filters: AppliedFilters
    sources: list[SourceApp]
