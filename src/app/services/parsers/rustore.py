import asyncio
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.async_api import BrowserContext

from app.core import config


class RustoreParser:
    _semaphore: asyncio.Semaphore | None = None

    @classmethod
    def _get_semaphore(cls) -> asyncio.Semaphore:
        if cls._semaphore is None:
            cls._semaphore = asyncio.Semaphore(3)
        return cls._semaphore

    @staticmethod
    async def _fetch_page(context: BrowserContext, category: str, page_num: int) -> list[str]:
        url = urljoin(config.RUSTORE_CATALOG_URL, f'{category}/page-{page_num}')

        async with RustoreParser._get_semaphore():
            page = await context.new_page()
            try:
                await page.goto(url, wait_until='networkidle')
                content = await page.content()
            finally:
                await page.close()

        soup = BeautifulSoup(content, 'lxml')
        links = soup.find_all('a', href=lambda h: h and h.startswith(config.RUSTORE_APP_NAME_PREFIX))

        return [link['href'].split('/')[-1] for link in links]

    @staticmethod
    async def parse_category(context: BrowserContext, category: str, page_limit: int = 10) -> list[str]:
        results = await asyncio.gather(
            *[RustoreParser._fetch_page(context, category, page) for page in range(1, page_limit + 1)]
        )

        return [app for page_apps in results for app in page_apps]
