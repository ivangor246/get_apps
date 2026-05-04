from pydantic import BaseModel

from .ollama import OllamaStatusSchema


class SystemStatusSchema(BaseModel):
    """Aggregated startup status for the backend and Ollama."""

    backend: str
    ollama: OllamaStatusSchema
