from pydantic import BaseModel, Field


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
