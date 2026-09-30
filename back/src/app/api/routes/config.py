from fastapi import APIRouter

from app.core.config import get_config, get_tunable_defaults, settings_store

from ..schemas.config import AppConfig, AppConfigPatch

router = APIRouter()


@router.get('/config', response_model=AppConfig)
async def read_config() -> AppConfig:
    """Return current effective config (defaults merged with saved overrides)."""
    cfg = get_config()
    return AppConfig(**{k: getattr(cfg, k) for k in get_tunable_defaults().keys()})


@router.put('/config', response_model=AppConfig)
async def write_config(patch: AppConfigPatch) -> AppConfig:
    """Merge patch into saved overrides; persists to saved_data/config.json."""
    existing = settings_store.load()
    updates = patch.model_dump(exclude_unset=True, exclude_none=False)
    merged = {**existing, **updates}
    settings_store.save(merged)
    cfg = get_config()
    return AppConfig(**{k: getattr(cfg, k) for k in get_tunable_defaults().keys()})


@router.get('/config/defaults', response_model=AppConfig)
async def read_config_defaults() -> AppConfig:
    """Return hardcoded defaults (ignoring any saved overrides)."""
    return AppConfig(**get_tunable_defaults())
