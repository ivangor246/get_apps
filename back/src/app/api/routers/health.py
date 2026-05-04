from fastapi import APIRouter

router = APIRouter()


@router.get('/health')
async def health() -> dict:
    """Liveness probe."""
    return {'status': 'ok'}
