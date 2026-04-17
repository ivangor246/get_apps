from app.services import RustoreService


async def run_rustore_tasks() -> None:
    await RustoreService.collect_all_categories()
