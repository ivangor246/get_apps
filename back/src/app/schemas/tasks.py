from pydantic import BaseModel, Field


class CollectCategoriesRequest(BaseModel):
    """Body for POST /tasks/collect-categories."""

    concurrency: int = Field(default=3, ge=1, le=16)


class CollectAppsRequest(BaseModel):
    """Body for POST /tasks/collect-apps: target DB plus optional categories run folder."""

    db_name: str = Field(..., min_length=1)
    folder_name: str | None = None
    concurrency: int = Field(default=3, ge=1, le=16)


class IndexRequest(BaseModel):
    """Body for POST /tasks/index: which DB to embed and concurrency knob."""

    db_name: str = Field(..., min_length=1)
    concurrency: int = Field(default=1, ge=1, le=16)
