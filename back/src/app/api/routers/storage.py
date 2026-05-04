from fastapi import APIRouter

from app.core import config
from app.schemas import CategoriesRunsResponse, DatabasesResponse

router = APIRouter()


@router.get('/databases', response_model=DatabasesResponse)
async def list_databases() -> DatabasesResponse:
    """List SQLite databases under saved_data/databases/ (by stem name)."""
    config.DATABASES_DIR.mkdir(parents=True, exist_ok=True)
    names = sorted(p.stem for p in config.DATABASES_DIR.glob('*.sqlite3'))
    return DatabasesResponse(databases=names)


@router.get('/categories-runs', response_model=CategoriesRunsResponse)
async def list_categories_runs() -> CategoriesRunsResponse:
    """List timestamped category-collection runs under saved_data/categories/."""
    config.CATEGORIES_DIR.mkdir(parents=True, exist_ok=True)
    runs = sorted((p.name for p in config.CATEGORIES_DIR.iterdir() if p.is_dir()), reverse=True)
    return CategoriesRunsResponse(runs=runs)
