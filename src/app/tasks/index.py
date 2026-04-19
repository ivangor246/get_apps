from app.services import EmbeddingIndexerService


async def run_index_task(db_name: str, batch_size: int = 32) -> None:
    """Embed every not-yet-indexed app in the given database."""
    await EmbeddingIndexerService(db_name=db_name, batch_size=batch_size).run()
