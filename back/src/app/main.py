from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core import config
from app.core.lifespan import lifespan


def create_app() -> FastAPI:
    """Build the FastAPI app."""

    app = FastAPI(
        title='get_apps',
        lifespan=lifespan,
        debug=config.DEBUG,
        docs_url=config.DOCS_URL,
        openapi_url=config.OPENAPI_URL,
        redoc_url=config.REDOC_URL,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_methods=['*'],
        allow_headers=['*'],
    )

    app.include_router(router)

    return app
