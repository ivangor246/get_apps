from functools import lru_cache
from pathlib import Path
from urllib.parse import urljoin


class Config:
    BASE_DIR: Path = Path(__file__).parent.parent.parent.parent
    DATA_DIR: Path = BASE_DIR / 'saved_data'

    RUSTORE_URL: str = 'www.rustore.ru'
    RUSTORE_CATALOG_URL: str = urljoin(RUSTORE_URL, 'catalog')
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


@lru_cache
def get_config() -> Config:
    return Config()


config = get_config()
