from pydantic import BaseModel


class OllamaStatusSchema(BaseModel):
    """Current state of the Ollama bring-up pipeline."""

    status: str
    detail: str | None = None
    model: str | None = None


class EmbeddingStatusSchema(BaseModel):
    """Availability of the local embedding model: ready, missing or downloading."""

    status: str
    detail: str | None = None
    model: str


class SystemStatusSchema(BaseModel):
    """Aggregated startup status for the backend, Ollama and the embedding model."""

    backend: str
    ollama: OllamaStatusSchema
    embedding: EmbeddingStatusSchema
