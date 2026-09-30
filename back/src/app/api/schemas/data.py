from pydantic import BaseModel


class DatabasesResponse(BaseModel):
    databases: list[str]


class CategoriesRunsResponse(BaseModel):
    runs: list[str]
