import logging
from datetime import datetime

from playwright.async_api import async_playwright

from app.core import config

from .parsers.rustore import RustoreParser

logger = logging.getLogger(__name__)


class RustoreService:
    @staticmethod
    async def collect_all_categories() -> None:
        timestamp = datetime.now().strftime('%d_%m_%Y_%H_%M_%S')
        output_dir = config.CATEGORIES_DIR / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context()

            try:
                for category in config.RUSTORE_CATEGORIES:
                    try:
                        apps = await RustoreParser.parse_category(context, category, config.RUSTORE_PAGES_COUNT)

                        output_file = output_dir / f'{category}.txt'
                        output_file.write_text('\n'.join(apps), encoding='utf-8')

                        logger.info('Category "%s" scanned successfully: %d apps found', category, len(apps))
                    except Exception:
                        logger.exception('Failed to scan category "%s"', category)
            finally:
                await browser.close()
