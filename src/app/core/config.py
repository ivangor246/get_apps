import json
from dataclasses import dataclass, field, fields
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

BASE_DIR: Path = Path(__file__).parent.parent.parent.parent
DATA_DIR: Path = BASE_DIR / 'saved_data'
CATEGORIES_DIR: Path = DATA_DIR / 'categories'
DATABASES_DIR: Path = DATA_DIR / 'databases'
CHROMA_DIR: Path = DATA_DIR / 'chroma'
CACHE_DIR: Path = BASE_DIR / 'cache_dir'
SETTINGS_FILE: Path = DATA_DIR / 'config.json'

CATEGORIES_TIMESTAMP_FORMAT: str = '%d_%m_%Y_%H_%M_%S'

RUSTORE_URL: str = 'https://www.rustore.ru'
RUSTORE_CATALOG_URL: str = urljoin(RUSTORE_URL, 'catalog/')
RUSTORE_APP_URL: str = urljoin(RUSTORE_URL, 'catalog/app/')
RUSTORE_APP_NAME_PREFIX: str = '/catalog/app/'
RUSTORE_CATEGORIES: list[str] = [
    'finance',
    'state',
    'tools',
    'transport',
    'purchases',
    'social',
    'entertainment',
    'adsandservices',
    'business',
    'health',
    'travelling',
    'education',
    'books',
    'lifestyle',
    'sport',
    'news',
    'parenting',
    'pets',
    'gambling',
    'foodanddrink',
]
RUSTORE_PAGES_COUNT: int = 10


@dataclass
class Config:
    """User-tunable runtime settings; defaults live here, overrides persist in saved_data/config.json."""

    OLLAMA_URL: str = 'http://localhost:11434'
    OLLAMA_LLM_MODEL: str = 'gemma3:1b'
    OLLAMA_TIMEOUT: float = 120.0
    OLLAMA_CONTEXT_SIZE: int = 10240

    EMBEDDING_MODEL: str = 'intfloat/multilingual-e5-large'
    EMBEDDING_DEVICE: str = 'cuda'
    EMBEDDING_DIM: int = 1024
    EMBEDDING_BATCH_SIZE: int = 8
    EMBEDDING_GPU_MEM_LIMIT_MB: int = 3072

    RAG_TOP_K: int = 10
    RAG_CANDIDATE_K: int = 500

    API_HOST: str = '127.0.0.1'
    API_PORT: int = 8000

    BASE_DIR: Path = field(default=BASE_DIR, init=False, repr=False)
    DATA_DIR: Path = field(default=DATA_DIR, init=False, repr=False)
    CATEGORIES_DIR: Path = field(default=CATEGORIES_DIR, init=False, repr=False)
    DATABASES_DIR: Path = field(default=DATABASES_DIR, init=False, repr=False)
    CHROMA_DIR: Path = field(default=CHROMA_DIR, init=False, repr=False)
    CACHE_DIR: Path = field(default=CACHE_DIR, init=False, repr=False)
    CATEGORIES_TIMESTAMP_FORMAT: str = field(default=CATEGORIES_TIMESTAMP_FORMAT, init=False, repr=False)
    RUSTORE_URL: str = field(default=RUSTORE_URL, init=False, repr=False)
    RUSTORE_CATALOG_URL: str = field(default=RUSTORE_CATALOG_URL, init=False, repr=False)
    RUSTORE_APP_URL: str = field(default=RUSTORE_APP_URL, init=False, repr=False)
    RUSTORE_APP_NAME_PREFIX: str = field(default=RUSTORE_APP_NAME_PREFIX, init=False, repr=False)
    RUSTORE_CATEGORIES: list[str] = field(default_factory=lambda: list(RUSTORE_CATEGORIES), init=False, repr=False)
    RUSTORE_PAGES_COUNT: int = field(default=RUSTORE_PAGES_COUNT, init=False, repr=False)


_TUNABLE_FIELDS: tuple[str, ...] = tuple(f.name for f in fields(Config) if f.init)


class SettingsStore:
    """Load/save user overrides for tunable Config fields as JSON on disk."""

    def __init__(self, path: Path = SETTINGS_FILE) -> None:
        self.path = path

    def load(self) -> dict[str, Any]:
        """Return saved overrides, filtered to known tunable fields."""
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding='utf-8'))
        except OSError, json.JSONDecodeError:
            return {}
        return {k: v for k, v in raw.items() if k in _TUNABLE_FIELDS}

    def save(self, overrides: dict[str, Any]) -> dict[str, Any]:
        """Persist overrides atomically; returns the filtered dict actually written."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        filtered = {k: v for k, v in overrides.items() if k in _TUNABLE_FIELDS}
        tmp = self.path.with_suffix(self.path.suffix + '.tmp')
        tmp.write_text(json.dumps(filtered, indent=2, ensure_ascii=False), encoding='utf-8')
        tmp.replace(self.path)
        get_config.cache_clear()
        return filtered


settings_store = SettingsStore()


@lru_cache
def get_config() -> Config:
    """Return the current Config instance with disk overrides applied."""
    return Config(**settings_store.load())


def get_tunable_defaults() -> dict[str, Any]:
    """Expose the hardcoded defaults (before any override) for the UI."""
    defaults = Config()
    return {name: getattr(defaults, name) for name in _TUNABLE_FIELDS}


def tunable_fields() -> tuple[str, ...]:
    return _TUNABLE_FIELDS


config = get_config()
