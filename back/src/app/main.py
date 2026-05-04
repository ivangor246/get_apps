from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.lifespan import lifespan


def create_app() -> FastAPI:
    """Build the FastAPI app."""

    app = FastAPI(
        title='get_apps',
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_methods=['*'],
        allow_headers=['*'],
    )

    app.include_router(router)

    return app
