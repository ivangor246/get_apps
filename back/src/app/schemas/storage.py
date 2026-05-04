from pydantic import BaseModel


class DatabasesResponse(BaseModel):
    """List of SQLite database names available under saved_data/databases/."""

    databases: list[str]


class CategoriesRunsResponse(BaseModel):
    """List of timestamped category-collection run folders under saved_data/categories/."""

    runs: list[str]
