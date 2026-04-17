from urllib.parse import urljoin

from bs4 import BeautifulSoup
from httpx import AsyncClient

from app.core import RustoreHTTPError, RustoreParseError, config


class RustoreParser:
    @staticmethod
    async def parse_category(client: AsyncClient, category: str, page_limit: int = 10) -> list[str]:
        apps = []

        for i in range(1, page_limit + 1):
            url = urljoin(config.RUSTORE_CATALOG_URL, f'{category}/page-{i}')

            response = await client.get(url, follow_redirects=True)

            if response.status_code != 200:
                raise RustoreHTTPError(response.status_code, url)

            soup = BeautifulSoup(response.text, 'lxml')
            links = soup.find_all('a', href=lambda h: h and h.startswith(config.RUSTORE_APP_NAME_PREFIX))

            if links is None:
                raise RustoreParseError(url)

            apps.extend(link['href'].split('/')[-1] for link in links)

        return apps
