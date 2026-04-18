import asyncio
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from playwright.async_api import BrowserContext

from app.core import config


class RustoreAppInfoParser:
    """Fetch a RuStore app page and extract detailed info via stable selectors."""

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

    @staticmethod
    async def _fetch_page(context: BrowserContext, app_id: str) -> str:
        """Load the app page with Playwright and return rendered HTML."""
        url = urljoin(config.RUSTORE_APP_URL, app_id)
        page = await context.new_page()
        try:
            await page.goto(url, wait_until='networkidle')
            return await page.content()
        finally:
            await page.close()

    @classmethod
    async def parse_app(cls, context: BrowserContext, app_id: str) -> dict:
        """Fetch and parse an app page; returns a dict matching AppInfo fields."""
        async with cls._get_semaphore():
            html = await cls._fetch_page(context, app_id)
        return cls._extract(html, app_id)

    @staticmethod
    def _extract(html: str, app_id: str) -> dict:
        """Parse HTML and extract all app fields into a plain dict."""
        soup = BeautifulSoup(html, 'lxml')
        url = urljoin(config.RUSTORE_APP_URL, app_id)

        main_info = soup.find(attrs={'data-testid': 'main-info'})
        ratings_count, reviews_count = _extract_ratings_reviews(soup)

        return {
            'app_id': app_id,
            'url': url,
            'name': _text_of(soup.find(attrs={'data-testid': 'name'})),
            'rating': _parse_float(_find_labeled_value(main_info, 'Рейтинг')),
            'ratings_count': ratings_count,
            'reviews_count': reviews_count,
            'downloads': _parse_count(_find_labeled_value(main_info, 'Скачиваний')),
            'size': _find_labeled_value(main_info, 'Размер'),
            'age': _find_labeled_value(main_info, 'Возраст'),
            'developer_name': _extract_developer_name(main_info),
            'developer_url': _extract_developer_url(main_info),
            'support_email': _extract_support_email(soup),
            'support_vk': _extract_support_link(soup, 'vk_outline'),
            'support_website': _extract_support_link(soup, 'globe_outline'),
            'min_android_version': _extract_min_android(soup),
            'description': _extract_description(soup),
            'screenshots': _extract_screenshots(soup),
            'categories': _extract_categories(soup),
            'requested_data': _extract_permissions(soup),
            'last_version': _extract_labeled_paragraph(soup, 'Версия:'),
            'last_update_date': _extract_labeled_paragraph(soup, 'Дата:'),
            'last_update_notes': _extract_update_notes(soup),
        }


def _text_of(node: Tag | None) -> str | None:
    """Return stripped text content of a node, or None."""
    if node is None:
        return None
    text = node.get_text(' ', strip=True)
    return text or None


def _find_labeled_value(root: Tag | None, label: str) -> str | None:
    """Find a span carrying the given label and return the adjacent value text."""
    if root is None:
        return None
    for span in root.find_all('span'):
        span_text = span.get_text(' ', strip=True).rstrip(':').strip()
        if span_text != label:
            continue
        if 'visually-hidden' in (span.get('class') or []):
            parent = span.parent
            if parent is None:
                continue
            clone = BeautifulSoup(str(parent), 'lxml')
            for hidden in clone.find_all(class_='visually-hidden'):
                hidden.decompose()
            for svg in clone.find_all('svg'):
                svg.decompose()
            value = clone.get_text(' ', strip=True)
            if value:
                return value
        else:
            li = span.find_parent('li') or span.parent
            if li is None:
                continue
            for sibling in reversed(li.find_all('span')):
                if sibling is span:
                    continue
                if 'visually-hidden' in (sibling.get('class') or []):
                    continue
                text = sibling.get_text(' ', strip=True)
                if text and text != label:
                    return text
    return None


def _extract_ratings_reviews(soup: BeautifulSoup) -> tuple[int | None, int | None]:
    """Extract (ratings_count, reviews_count); reviews_count may be None."""
    ratings_count: int | None = None
    reviews_count: int | None = None

    for span in soup.find_all('span'):
        text = span.get_text(' ', strip=True)
        if not text:
            continue
        if 'отзыв' in text and reviews_count is None:
            parts = re.split(r'[・·•]|\s-\s', text)
            for part in parts:
                if 'отзыв' in part:
                    reviews_count = _parse_count(part)
                elif 'оценок' in part and ratings_count is None:
                    ratings_count = _parse_count(part)
        elif 'оценок' in text and ratings_count is None and 'млн оценок' in text or ('тыс оценок' in text) or (
            re.search(r'\d\s*оценок', text) and 'оценок' == text.split()[-1].replace(',', '')
        ):
            ratings_count = _parse_count(text)

    if ratings_count is None:
        for span in soup.find_all('span'):
            text = span.get_text(' ', strip=True)
            if text and 'оценок' in text and len(text) < 40:
                ratings_count = _parse_count(text)
                if ratings_count is not None:
                    break

    return ratings_count, reviews_count


def _extract_developer_name(root: Tag | None) -> str | None:
    """Find the developer link in the main-info block and return its text."""
    link = _find_developer_link(root)
    return _text_of(link)


def _extract_developer_url(root: Tag | None) -> str | None:
    """Find the developer link in the main-info block and return absolute URL."""
    link = _find_developer_link(root)
    if link is None or not link.get('href'):
        return None
    return urljoin(config.RUSTORE_URL, link['href'])


def _find_developer_link(root: Tag | None) -> Tag | None:
    """Locate the <a data-testid='link'> pointing at /catalog/developer/ within root."""
    if root is None:
        return None
    for a in root.find_all('a', attrs={'data-testid': 'link'}):
        href = a.get('href') or ''
        if '/catalog/developer/' in href:
            return a
    return None


def _extract_support_email(soup: BeautifulSoup) -> str | None:
    """Find the first mailto support link and return the email."""
    link = soup.find('a', href=lambda h: h and h.startswith('mailto:'))
    if link is None:
        return None
    return link['href'].removeprefix('mailto:').strip() or None


def _extract_support_link(soup: BeautifulSoup, icon_name: str) -> str | None:
    """Find a support block whose svg icon ends with #icon_name and return its text."""
    for use in soup.find_all('use'):
        href = use.get('href') or use.get('xlink:href') or ''
        if not href.endswith(f'#{icon_name}'):
            continue
        container = use.find_parent(lambda tag: tag.name in ('div', 'a') and tag.find('p') is not None)
        if container is None:
            continue
        p = container.find('p')
        if p is not None:
            text = p.get_text(' ', strip=True)
            if text:
                return text
    return None


def _extract_min_android(soup: BeautifulSoup) -> str | None:
    """Find 'Минимальная версия Android: X' text and return the captured value."""
    for node in soup.find_all(string=re.compile(r'Минимальная версия Android')):
        parent_text = node.parent.get_text(' ', strip=True) if node.parent else str(node)
        match = re.search(r'Минимальная версия Android\s*:?\s*([\w.+]+)', parent_text)
        if match:
            return match.group(1)
    return None


def _extract_description(soup: BeautifulSoup) -> str | None:
    """Return the first <p> text inside the description block."""
    block = soup.find(attrs={'data-testid': 'description'})
    if block is None:
        return None
    p = block.find('p')
    return _text_of(p)


def _extract_screenshots(soup: BeautifulSoup) -> list[str] | None:
    """Return list of src URLs for images inside the screenshots block."""
    block = soup.find(attrs={'data-testid': 'screenshots'})
    if block is None:
        return None
    urls: list[str] = []
    for img in block.find_all('img'):
        src = img.get('src')
        if src and src not in urls:
            urls.append(src)
    return urls or None


def _extract_categories(soup: BeautifulSoup) -> list[str] | None:
    """Collect unique labels/categories/tags text from chips blocks."""
    values: list[str] = []
    seen: set[str] = set()
    for chips in soup.find_all(attrs={'data-testid': 'chips'}):
        for node in chips.find_all(attrs={'data-testid': True}):
            testid = node.get('data-testid', '')
            if not (testid.startswith('category-') or testid.startswith('tag-') or testid.startswith('label-')):
                continue
            text = _visible_text(node)
            if text and text not in seen:
                seen.add(text)
                values.append(text)
    return values or None


def _extract_permissions(soup: BeautifulSoup) -> list[str] | None:
    """Collect text of each element marked with data-testid='permission'."""
    values: list[str] = []
    for node in soup.find_all(attrs={'data-testid': 'permission'}):
        text = node.get_text(' ', strip=True)
        if text:
            values.append(text)
    return values or None


def _extract_labeled_paragraph(soup: BeautifulSoup, label: str) -> str | None:
    """Find a <p> whose visually-hidden child text matches label; return remaining text."""
    for hidden in soup.find_all('span', class_='visually-hidden'):
        hidden_text = hidden.get_text(' ', strip=True).rstrip(':').rstrip()
        if hidden_text.rstrip(':') != label.rstrip(':'):
            continue
        parent = hidden.parent
        if parent is None:
            continue
        full = parent.get_text(' ', strip=True)
        cleaned = full.replace(hidden.get_text(' ', strip=True), '', 1).strip()
        if cleaned:
            return cleaned
    return None


def _extract_update_notes(soup: BeautifulSoup) -> str | None:
    """Locate the first 'Что нового' section and return the non-metadata paragraph text."""
    heading = soup.find(lambda tag: tag.name in ('h2', 'div') and tag.get_text(strip=True) == 'Что нового')
    if heading is None or heading.parent is None:
        return None
    container = heading.parent
    for p in container.find_all('p', recursive=False):
        hidden = p.find('span', class_='visually-hidden')
        if hidden is not None:
            continue
        text = p.get_text(' ', strip=True)
        if text:
            return text
    return None


def _visible_text(node: Tag) -> str | None:
    """Return node text with visually-hidden spans removed."""
    clone = BeautifulSoup(str(node), 'lxml')
    for hidden in clone.find_all('span', class_='visually-hidden'):
        hidden.decompose()
    text = clone.get_text(' ', strip=True)
    return text or None


def _parse_float(text: str | None) -> float | None:
    """Parse a decimal with comma or dot separator into a float."""
    if not text:
        return None
    match = re.search(r'\d+(?:[.,]\d+)?', text)
    if not match:
        return None
    try:
        return float(match.group().replace(',', '.'))
    except ValueError:
        return None


def _parse_count(text: str | None) -> int | None:
    """Parse counts like '3,0 млн', '30 млн +', '500 тыс', '88 145' into int."""
    if not text:
        return None
    t = text.replace('\xa0', ' ').replace('+', ' ')
    multiplier = 1
    for word, m in (('млрд', 1_000_000_000), ('млн', 1_000_000), ('тыс', 1_000)):
        if word in t:
            multiplier = m
            break
    if multiplier > 1:
        match = re.search(r'\d+(?:[.,]\d+)?', t)
        if not match:
            return None
        return int(float(match.group().replace(',', '.')) * multiplier)
    match = re.search(r'\d[\d\s]*\d|\d', t)
    if not match:
        return None
    try:
        return int(match.group().replace(' ', ''))
    except ValueError:
        return None
