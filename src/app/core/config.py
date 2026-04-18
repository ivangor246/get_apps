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


@lru_cache
def get_config() -> Config:
    return Config()


config = get_config()
