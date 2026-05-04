from pydantic import BaseModel, Field


class OllamaStatusSchema(BaseModel):
    """Current state of the Ollama bring-up pipeline."""

    status: str
    detail: str | None = None
    model: str | None = None


class SystemStatusSchema(BaseModel):
    """Aggregated startup status for the backend and Ollama."""

    backend: str
    ollama: OllamaStatusSchema


class OllamaModelInfo(BaseModel):
    """One Ollama model entry: name plus its downloaded and currently-loaded state."""

    name: str
    downloaded: bool
    loaded: bool


class OllamaModelsResponse(BaseModel):
    """Listing of locally available Ollama models plus the currently configured choice."""

    current: str
    models: list[OllamaModelInfo]


class OllamaModelLoadRequest(BaseModel):
    """Request body for POST /ollama/models/load."""

    model: str = Field(..., min_length=1)


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
    intent: str
    language: str
    iterations: int
