from __future__ import annotations

import asyncio
import logging

from fastembed import TextEmbedding

from .config import config

logger = logging.getLogger(__name__)


class TextEmbedder:
    """Async wrapper over fastembed; applies e5-style passage/query prefixes.

    Configured for intfloat/multilingual-e5-large by default: that model requires
    ``passage:`` / ``query:`` prefixes and is the source of those strings here.
    """

    _PASSAGE_PREFIX = 'passage: '
    _QUERY_PREFIX = 'query: '

    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
        cache_dir: str | None = None,
    ) -> None:
        self._model_name = model_name or config.EMBEDDING_MODEL
        self._device = device or config.EMBEDDING_DEVICE
        self._cache_dir = cache_dir or str(config.CACHE_DIR)
        providers = self._providers_for(self._device)
        config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(
            'Loading embedding model %s (providers=%s, cache_dir=%s)',
            self._model_name, providers, self._cache_dir,
        )
        self._model = TextEmbedding(
            model_name=self._model_name,
            cache_dir=self._cache_dir,
            providers=providers,
        )

    async def embed_passages(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Encode indexable documents with the e5 ``passage:`` prefix."""
        if not texts:
            return []
        prefixed = [f'{self._PASSAGE_PREFIX}{t}' for t in texts]
        return await asyncio.to_thread(self._encode_sync, prefixed, batch_size)

    async def embed_query(self, text_value: str) -> list[float]:
        """Encode a single search query with the e5 ``query:`` prefix."""
        prefixed = [f'{self._QUERY_PREFIX}{text_value}']
        vectors = await asyncio.to_thread(self._encode_sync, prefixed, 1)
        return vectors[0]

    def _encode_sync(self, texts: list[str], batch_size: int) -> list[list[float]]:
        vectors = list(self._model.embed(texts, batch_size=batch_size))
        return [vec.tolist() for vec in vectors]

    @staticmethod
    def _providers_for(device: str) -> list[str]:
        if device.lower() == 'cuda':
            return ['CUDAExecutionProvider', 'CPUExecutionProvider']
        return ['CPUExecutionProvider']
