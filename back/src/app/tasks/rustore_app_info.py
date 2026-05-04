from app.services import RustoreAppInfoService


async def run_rustore_app_info_tasks(db_name: str, folder_name: str | None = None, concurrency: int = 3) -> None:
    """Run the RuStore app-info collection pipeline into the given database."""
    await RustoreAppInfoService(db_name=db_name, folder_name=folder_name, concurrency=concurrency).run()
