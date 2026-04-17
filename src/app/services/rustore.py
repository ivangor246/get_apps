import logging

from httpx import AsyncClient

from app.core import RustoreError, config

from .parsers.rustore import RustoreParser

logger = logging.getLogger(__name__)


class RustoreService:
    @staticmethod
    async def collect_all_categories() -> None:
        config.CATEGORIES_DIR.mkdir(parents=True, exist_ok=True)

        async with AsyncClient() as client:
            for category in config.RUSTORE_CATEGORIES:
                try:
                    apps = await RustoreParser.parse_category(client, category, config.RUSTORE_PAGES_COUNT)

                    output_file = config.CATEGORIES_DIR / f'{category}.txt'
                    output_file.write_text('\n'.join(apps), encoding='utf-8')

                    logger.info('Category "%s" scanned successfully: %d apps found', category, len(apps))
                except RustoreError:
                    logger.exception('Failed to scan category "%s"', category)
