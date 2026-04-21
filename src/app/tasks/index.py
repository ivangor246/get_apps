from app.core import TextEmbedder
from app.services import EmbeddingIndexerService


async def run_index_task(db_name: str, batch_size: int = 32, concurrency: int = 1) -> None:
    """Embed every not-yet-indexed app in the given database."""
    embedder = TextEmbedder()
    await EmbeddingIndexerService(
        db_name=db_name, embedder=embedder, batch_size=batch_size, concurrency=concurrency
    ).run()
