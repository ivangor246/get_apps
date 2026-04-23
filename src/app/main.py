import uvicorn

from app.core.config import get_config


def main() -> None:
    """Start the FastAPI web server; all interaction happens via the web UI."""
    cfg = get_config()
    uvicorn.run(
        'app.api.app:create_app',
        factory=True,
        host=cfg.API_HOST,
        port=cfg.API_PORT,
        log_level='info',
    )


if __name__ == '__main__':
    main()
