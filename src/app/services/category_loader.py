import logging
from datetime import datetime
from pathlib import Path

from app.core import config

logger = logging.getLogger(__name__)


class CategoryLoader:
    """Locate and read collected category files, returning unique app IDs."""

    @staticmethod
    def resolve_folder(folder_name: str | None = None) -> Path:
        """Return target timestamp folder; latest by name if folder_name is None."""
        if folder_name is not None:
            path = config.CATEGORIES_DIR / folder_name
            if not path.is_dir():
                raise FileNotFoundError(f'Categories folder not found: {path}')
            return path

        if not config.CATEGORIES_DIR.is_dir():
            raise FileNotFoundError(f'Categories directory does not exist: {config.CATEGORIES_DIR}')

        candidates: list[tuple[datetime, Path]] = []
        for entry in config.CATEGORIES_DIR.iterdir():
            if not entry.is_dir():
                continue
            try:
                ts = datetime.strptime(entry.name, config.CATEGORIES_TIMESTAMP_FORMAT)
            except ValueError:
                continue
            candidates.append((ts, entry))

        if not candidates:
            raise FileNotFoundError(f'No timestamped subfolders in {config.CATEGORIES_DIR}')

        candidates.sort(key=lambda item: item[0])
        return candidates[-1][1]

    @staticmethod
    def load_unique_app_ids(folder: Path) -> list[str]:
        """Read all *.txt files in folder and return a sorted list of unique app IDs."""
        unique: set[str] = set()
        for txt in folder.glob('*.txt'):
            for line in txt.read_text(encoding='utf-8').splitlines():
                app_id = line.strip()
                if app_id:
                    unique.add(app_id)

        logger.info('Loaded %d unique app IDs from %s', len(unique), folder)
        return sorted(unique)
