import uvicorn

from app.api import create_app
from app.core import config


async def run_serve_task(db_name: str, host: str | None = None, port: int | None = None) -> None:
    """Serve the RAG FastAPI app via uvicorn bound to the given database."""
    app = create_app(db_name)
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host=host or config.API_HOST,
            port=port or config.API_PORT,
            log_level='info',
        )
    )
    await server.serve()
