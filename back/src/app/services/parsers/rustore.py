import asyncio
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.async_api import BrowserContext

from app.core import config


class RustoreParser:
    """Scrape RuStore category listing pages and extract app IDs from anchor links."""

    _semaphore: asyncio.Semaphore | None = None

    @classmethod
    def set_concurrency(cls, limit: int) -> None:
        """Configure the shared semaphore controlling parallel page fetches."""

        cls._semaphore = asyncio.Semaphore(limit)

    @classmethod
    def _get_semaphore(cls) -> asyncio.Semaphore:
        """Return the shared semaphore, initializing a default (3) if unset."""

        if cls._semaphore is None:
            cls._semaphore = asyncio.Semaphore(3)
        return cls._semaphore

    @classmethod
    async def _fetch_page(
        cls,
        context: BrowserContext,
        category: str,
        page_num: int,
    ) -> list[str]:
        """Load one paginated category page in a fresh tab and return the app IDs found on it."""

        url = urljoin(config.RUSTORE_CATALOG_URL, f'{category}/page-{page_num}')

        async with cls._get_semaphore():
            page = await context.new_page()
            try:
                await page.goto(url, wait_until='networkidle')
                content = await page.content()
            finally:
                await page.close()

        soup = BeautifulSoup(content, 'lxml')
        links = soup.find_all('a', href=lambda h: h and h.startswith(config.RUSTORE_APP_NAME_PREFIX))

        return [link['href'].split('/')[-1] for link in links]

    @classmethod
    async def parse_category(
        cls,
        context: BrowserContext,
        category: str,
        page_limit: int = 10,
    ) -> list[str]:
        """Fetch the first `page_limit` pages of a category in parallel and flatten app IDs into one list."""

        results = await asyncio.gather(*[cls._fetch_page(context, category, page) for page in range(1, page_limit + 1)])
        return [app for page_apps in results for app in page_apps]
