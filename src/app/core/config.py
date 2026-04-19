import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import urljoin


class Config:
    BASE_DIR: Path = Path(__file__).parent.parent.parent.parent
    DATA_DIR: Path = BASE_DIR / 'saved_data'
    CATEGORIES_DIR: Path = DATA_DIR / 'categories'
    DATABASES_DIR: Path = DATA_DIR / 'databases'

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

    OLLAMA_URL: str = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    OLLAMA_LLM_MODEL: str = os.getenv('OLLAMA_LLM_MODEL', 'gemma4:e2b')
    OLLAMA_EMBEDDING_MODEL: str = os.getenv('OLLAMA_EMBEDDING_MODEL', 'bge-m3')
    OLLAMA_TIMEOUT: float = float(os.getenv('OLLAMA_TIMEOUT', '120'))

    EMBEDDING_DIM: int = int(os.getenv('EMBEDDING_DIM', '1024'))
    RAG_TOP_K: int = int(os.getenv('RAG_TOP_K', '20'))
    RAG_CANDIDATE_K: int = int(os.getenv('RAG_CANDIDATE_K', '500'))

    API_HOST: str = os.getenv('API_HOST', '127.0.0.1')
    API_PORT: int = int(os.getenv('API_PORT', '8000'))


@lru_cache
def get_config() -> Config:
    return Config()


config = get_config()
