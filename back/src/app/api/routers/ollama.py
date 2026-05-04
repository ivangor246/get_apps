from fastapi import APIRouter, HTTPException, Request

from app.core import config
from app.core.exceptions import OllamaError, OllamaHTTPError
from app.core.ollama import OllamaClient
from app.schemas import OllamaModelInfo, OllamaModelLoadRequest, OllamaModelsResponse

router = APIRouter(prefix='/ollama')


@router.get('/models', response_model=OllamaModelsResponse)
async def list_ollama_models(request: Request) -> OllamaModelsResponse:
    """List models available in the local Ollama instance with their loaded state."""
    client: OllamaClient = request.app.state.ollama
    current = config.OLLAMA_LLM_MODEL
    try:
        local = await client.list_local_models()
    except OllamaError as err:
        raise HTTPException(status_code=503, detail=f'Ollama unreachable: {err}') from err
    try:
        loaded = set(await client.list_loaded_models())
    except OllamaError:
        loaded = set()
    models = [OllamaModelInfo(name=name, downloaded=True, loaded=name in loaded) for name in local]
    if current and current not in local:
        models.insert(0, OllamaModelInfo(name=current, downloaded=False, loaded=False))
    return OllamaModelsResponse(current=current, models=models)


@router.post('/models/load', status_code=204)
async def load_ollama_model(request: Request, body: OllamaModelLoadRequest) -> None:
    """Pin the specified model into Ollama memory by issuing an empty generate call."""
    client: OllamaClient = request.app.state.ollama
    try:
        await client.load_model(body.model)
    except OllamaHTTPError as err:
        raise HTTPException(status_code=err.status_code, detail=err.body) from err
    except OllamaError as err:
        raise HTTPException(status_code=503, detail=str(err)) from err
