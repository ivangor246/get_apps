from __future__ import annotations

from types import TracebackType

import httpx

from ..config import config, get_config
from ..exceptions import OllamaError, OllamaHTTPError


class OllamaClient:
    """Async client for the Ollama HTTP API: LLM generation."""

    def __init__(
        self,
        base_url: str | None = None,
        llm_model: str | None = None,
        timeout: float | None = None,
    ):
        self._base_url = (base_url or config.OLLAMA_URL).rstrip('/')
        self._llm_model_override = llm_model
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
        model: str | None = None,
        context_size: int | None = None,
        timeout: float | None = None,
    ) -> str:
        """Generate a completion; per-call overrides take precedence over config defaults."""
        cfg = get_config()
        payload: dict = {
            'model': model or self._llm_model_override or cfg.OLLAMA_LLM_MODEL,
            'prompt': prompt,
            'stream': False,
            'options': {'num_ctx': context_size or cfg.OLLAMA_CONTEXT_SIZE},
        }
        if system is not None:
            payload['system'] = system
        if json_format:
            payload['format'] = 'json'
        data = await self._post_json('/api/generate', payload, timeout=timeout)
        response = data.get('response')
        if not isinstance(response, str):
            raise OllamaError(f'Unexpected generate response: {data!r}')
        return response

    async def list_local_models(self) -> list[str]:
        """Return names of models pulled to disk (GET /api/tags)."""
        data = await self._get_json('/api/tags')
        return [str(item.get('name', '')) for item in data.get('models', []) if item.get('name')]

    async def list_loaded_models(self) -> list[str]:
        """Return names of models currently resident in memory (GET /api/ps)."""
        data = await self._get_json('/api/ps')
        return [str(item.get('name', '')) for item in data.get('models', []) if item.get('name')]

    async def load_model(self, name: str) -> None:
        """Force a model into memory by issuing an empty generate with keep_alive and configured context."""
        await self._post_json(
            '/api/generate',
            {
                'model': name,
                'prompt': '',
                'stream': False,
                'keep_alive': '5m',
                'options': {'num_ctx': get_config().OLLAMA_CONTEXT_SIZE},
            },
        )

    async def _get_json(self, endpoint: str) -> dict:
        try:
            response = await self._client.get(endpoint)
        except httpx.HTTPError as err:
            raise OllamaError(f'Ollama request failed: {type(err).__name__}: {err}') from err
        if response.status_code >= 400:
            raise OllamaHTTPError(response.status_code, endpoint, response.text)
        return response.json()

    async def _post_json(self, endpoint: str, payload: dict, *, timeout: float | None = None) -> dict:
        try:
            kwargs: dict = {'json': payload}
            if timeout is not None:
                kwargs['timeout'] = timeout
            response = await self._client.post(endpoint, **kwargs)
        except httpx.HTTPError as err:
            raise OllamaError(f'Ollama request failed: {type(err).__name__}: {err}') from err
        if response.status_code >= 400:
            raise OllamaHTTPError(response.status_code, endpoint, response.text)
        return response.json()
