import asyncio
import logging

from playwright.async_api import async_playwright
from sqlalchemy import select

from app.core.storage import build_engine, build_sessionmaker, init_db
from app.models import AppInfo

from .category_loader import CategoryLoader
from .parsers import RustoreAppInfoParser

logger = logging.getLogger(__name__)


class RustoreAppInfoService:
    """Orchestrate parsing of RuStore app pages into a SQLite database."""

    def __init__(
        self,
        db_name: str,
        folder_name: str | None = None,
        concurrency: int = 3,
    ) -> None:
        self.db_name = db_name
        self.folder_name = folder_name
        self.concurrency = concurrency

    async def run(self) -> None:
        """Resolve target folder, load app IDs, and persist each parsed app page."""

        folder = CategoryLoader.resolve_folder(self.folder_name)
        all_ids = CategoryLoader.load_unique_app_ids(folder)

        engine = build_engine(self.db_name)
        session_factory = build_sessionmaker(engine)
        await init_db(engine)

        processed = await self._load_processed_ids(session_factory)
        pending = [app_id for app_id in all_ids if app_id not in processed]
        logger.info('Apps to process: %d (already in DB: %d)', len(pending), len(processed))

        if not pending:
            await engine.dispose()
            return

        RustoreAppInfoParser.set_concurrency(self.concurrency)

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context()

            try:
                tasks = [self._process_app(context, session_factory, app_id) for app_id in pending]
                await asyncio.gather(*tasks)
            finally:
                await browser.close()
                await engine.dispose()

    @staticmethod
    async def _load_processed_ids(session_factory) -> set[str]:
        """Return the set of app IDs already stored in the database."""

        async with session_factory() as session:
            result = await session.execute(select(AppInfo.app_id))
            return {row[0] for row in result.all()}

    @staticmethod
    async def _process_app(context, session_factory, app_id: str) -> None:
        """Parse a single app page and commit it in its own session for resumability."""

        try:
            data = await RustoreAppInfoParser.parse_app(context, app_id)
        except Exception:
            logger.exception('Failed to parse app "%s"', app_id)
            return

        try:
            async with session_factory() as session:
                session.add(AppInfo(**data))
                await session.commit()
            logger.info('Saved "%s" (%s)', data.get('name') or app_id, app_id)
        except Exception:
            logger.exception('Failed to save app "%s"', app_id)
