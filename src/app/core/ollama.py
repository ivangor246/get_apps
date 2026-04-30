from __future__ import annotations

from types import TracebackType

import httpx

from .config import config
from .exceptions import OllamaError, OllamaHTTPError


class OllamaClient:
    """Async client for the Ollama HTTP API: LLM generation."""

    def __init__(
        self,
        base_url: str | None = None,
        llm_model: str | None = None,
        timeout: float | None = None,
    ):
        self._base_url = (base_url or config.OLLAMA_URL).rstrip('/')
        self._llm_model = llm_model or config.OLLAMA_LLM_MODEL
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout or config.OLLAMA_TIMEOUT,
        )

    async def __aenter__(self) -> OllamaClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Release the underlying HTTP client."""
        await self._client.aclose()

    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        json_format: bool = False,
    ) -> str:
        """Generate a completion; set json_format=True to force JSON output."""
        payload: dict = {
            'model': self._llm_model,
            'prompt': prompt,
            'stream': False,
        }
        if system is not None:
            payload['system'] = system
        if json_format:
            payload['format'] = 'json'
        data = await self._post_json('/api/generate', payload)
        response = data.get('response')
        if not isinstance(response, str):
            raise OllamaError(f'Unexpected generate response: {data!r}')
        return response

    async def _post_json(self, endpoint: str, payload: dict) -> dict:
        try:
            response = await self._client.post(endpoint, json=payload)
        except httpx.HTTPError as err:
            raise OllamaError(f'Ollama request failed: {type(err).__name__}: {err}') from err
        if response.status_code >= 400:
            raise OllamaHTTPError(response.status_code, endpoint, response.text)
        return response.json()
