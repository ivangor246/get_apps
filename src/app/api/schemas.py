from pydantic import BaseModel, Field


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
