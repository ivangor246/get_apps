import logging
from datetime import datetime

from playwright.async_api import async_playwright

from app.core import config

from .parsers import RustoreParser

logger = logging.getLogger(__name__)


class RustoreService:
    """Drives RuStore category scraping via Playwright and persists app IDs per run."""

    @staticmethod
    async def collect_all_categories(concurrency: int = 3) -> None:
        """Scrape every configured RuStore category and dump app IDs into a timestamped run folder."""

        timestamp = datetime.now().strftime('%d_%m_%Y_%H_%M_%S')
        output_dir = config.CATEGORIES_DIR / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)

        RustoreParser.set_concurrency(concurrency)

        async with async_playwright() as p:
            async with await p.chromium.launch() as browser:
                context = await browser.new_context()

                for category in config.RUSTORE_CATEGORIES:
                    try:
                        apps = await RustoreParser.parse_category(
                            context,
                            category,
                            config.RUSTORE_PAGES_COUNT,
                        )

                        output_file = output_dir / f'{category}.txt'
                        output_file.write_text('\n'.join(apps), encoding='utf-8')

                        logger.info('Category "%s" scanned successfully: %d apps found', category, len(apps))
                    except Exception:
                        logger.exception('Failed to scan category "%s"', category)
