from fastapi import APIRouter

from . import config, data, embedding, ollama, rag, system, tasks

router = APIRouter()
router.include_router(system.router)
router.include_router(config.router)
router.include_router(ollama.router)
router.include_router(embedding.router)
router.include_router(data.router)
router.include_router(tasks.router)
router.include_router(rag.router)
