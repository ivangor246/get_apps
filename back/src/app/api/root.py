from fastapi import APIRouter

from .routers.config import router as config_router
from .routers.health import router as health_router
from .routers.ollama import router as ollama_router
from .routers.rag import router as rag_router
from .routers.storage import router as storage_router
from .routers.system import router as system_router
from .routers.tasks import router as tasks_router

ROUTERS: list[APIRouter] = [
    config_router,
    health_router,
    ollama_router,
    rag_router,
    storage_router,
    system_router,
    tasks_router,
]

router = APIRouter(prefix='/api')

for r in ROUTERS:
    router.include_router(r)
