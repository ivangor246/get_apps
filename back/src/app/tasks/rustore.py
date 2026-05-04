from app.services import RustoreService


async def run_rustore_tasks(
    concurrency: int = 3,
) -> None:
    """Run the RuStore category-collection pipeline across all configured categories."""

    await RustoreService.collect_all_categories(
        concurrency=concurrency,
    )
