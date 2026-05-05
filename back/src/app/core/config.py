from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import urljoin

_BASE_DIR: Path = Path(__file__).parent.parent.parent.parent
_DATA_DIR: Path = _BASE_DIR / 'saved_data'
_RUSTORE_URL: str = 'https://www.rustore.ru'


@dataclass(frozen=True)
class Config:
    """Immutable runtime settings; values are fixed at process start."""

    API_HOST: str = '127.0.0.1'
    API_PORT: int = 8000

    DOCS_URL: str = '/api/docs'
    OPENAPI_URL: str = '/api/docs.json'
    REDOC_URL: str = '/api/redoc'

    DEBUG: bool = True

    BASE_DIR: Path = _BASE_DIR
    DATA_DIR: Path = _DATA_DIR
    CATEGORIES_DIR: Path = _DATA_DIR / 'categories'
    DATABASES_DIR: Path = _DATA_DIR / 'databases'
    CHROMA_DIR: Path = _DATA_DIR / 'chroma'
    CACHE_DIR: Path = _BASE_DIR / 'cache_dir'

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

    CATEGORIES_TIMESTAMP_FORMAT: str = '%d_%m_%Y_%H_%M_%S'

    RUSTORE_URL: str = _RUSTORE_URL
    RUSTORE_CATALOG_URL: str = urljoin(_RUSTORE_URL, 'catalog/')
    RUSTORE_APP_URL: str = urljoin(_RUSTORE_URL, 'catalog/app/')
    RUSTORE_APP_NAME_PREFIX: str = '/catalog/app/'
    RUSTORE_CATEGORIES: tuple[str, ...] = (
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
    )
    RUSTORE_PAGES_COUNT: int = 10


@lru_cache
def get_config() -> Config:
    """Return the single Config instance; values do not change after startup."""
    return Config()


config = get_config()
