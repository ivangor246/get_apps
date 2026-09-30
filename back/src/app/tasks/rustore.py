from app.services import RustoreService


async def run_rustore_tasks(concurrency: int = 3) -> None:
    await RustoreService.collect_all_categories(concurrency=concurrency)
