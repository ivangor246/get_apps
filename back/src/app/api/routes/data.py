from fastapi import APIRouter

from app.core.config import get_config

from ..schemas.data import CategoriesRunsResponse, DatabasesResponse

router = APIRouter()


@router.get('/databases', response_model=DatabasesResponse)
async def list_databases() -> DatabasesResponse:
    """List SQLite databases under saved_data/databases/ (by stem name)."""
    cfg = get_config()
    cfg.DATABASES_DIR.mkdir(parents=True, exist_ok=True)
    names = sorted(p.stem for p in cfg.DATABASES_DIR.glob('*.sqlite3'))
    return DatabasesResponse(databases=names)


@router.get('/categories-runs', response_model=CategoriesRunsResponse)
async def list_categories_runs() -> CategoriesRunsResponse:
    """List timestamped category-collection runs under saved_data/categories/."""
    cfg = get_config()
    cfg.CATEGORIES_DIR.mkdir(parents=True, exist_ok=True)
    runs = sorted((p.name for p in cfg.CATEGORIES_DIR.iterdir() if p.is_dir()), reverse=True)
    return CategoriesRunsResponse(runs=runs)
