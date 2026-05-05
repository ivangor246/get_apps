from pydantic import BaseModel, Field


class OllamaStatusSchema(BaseModel):
    """Current state of the Ollama bring-up pipeline."""

    status: str
    detail: str | None = None


class OllamaModelInfo(BaseModel):
    """One Ollama model entry: name plus its downloaded and currently-loaded state."""

    name: str
    downloaded: bool
    loaded: bool


class OllamaModelsResponse(BaseModel):
    """Listing of locally available Ollama models."""

    models: list[OllamaModelInfo]


class OllamaModelLoadRequest(BaseModel):
    """Request body for POST /ollama/models/load."""

    model: str = Field(..., min_length=1)
