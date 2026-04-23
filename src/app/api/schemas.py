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


class CollectCategoriesRequest(BaseModel):
    concurrency: int = Field(default=3, ge=1, le=16)


class CollectAppsRequest(BaseModel):
    db_name: str = Field(..., min_length=1)
    folder_name: str | None = None
    concurrency: int = Field(default=3, ge=1, le=16)


class IndexRequest(BaseModel):
    db_name: str = Field(..., min_length=1)
    batch_size: int = Field(default=32, ge=1, le=1024)
    concurrency: int = Field(default=1, ge=1, le=16)


class JobCreated(BaseModel):
    job_id: str
    kind: str


class JobSnapshot(BaseModel):
    id: str
    kind: str
    status: str
    progress_current: int
    progress_total: int | None = None
    error: str | None = None
    created_at: float
    started_at: float | None = None
    finished_at: float | None = None


class DatabasesResponse(BaseModel):
    databases: list[str]


class CategoriesRunsResponse(BaseModel):
    runs: list[str]


class RAGQueryRequest(BaseModel):
    """Body for POST /rag/query."""

    db_name: str = Field(..., min_length=1, description='SQLite DB / Chroma collection to query.')
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
