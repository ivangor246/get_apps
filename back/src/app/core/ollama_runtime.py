from __future__ import annotations

import asyncio
import logging
import shutil
from dataclasses import dataclass
from enum import Enum

import httpx

from .config import get_config
from .exceptions import OllamaError
from .ollama import OllamaClient

logger = logging.getLogger('app')


class OllamaStatus(str, Enum):
    """Lifecycle states of the local Ollama bring-up pipeline."""

    PENDING = 'pending'
    STARTING_SERVER = 'starting_server'
    CHECKING_MODEL = 'checking_model'
    MODEL_MISSING = 'model_missing'
    WARMING_UP = 'warming_up'
    READY = 'ready'
    ERROR = 'error'


@dataclass
class OllamaState:
    """Snapshot of the runtime: current status plus a human-readable detail."""

    status: OllamaStatus = OllamaStatus.PENDING
    detail: str | None = None
    model: str | None = None


class OllamaRuntime:
    """Spawns ollama serve if needed, verifies the configured model, warms it up."""

    _PROBE_TIMEOUT = 1.0
    _TAGS_TIMEOUT = 5.0
    _SPAWN_WAIT_TIMEOUT = 15.0
    _SPAWN_POLL_INTERVAL = 0.5
    _STOP_TIMEOUT = 5.0

    def __init__(self, client: OllamaClient) -> None:
        cfg = get_config()
        self._client = client
        self._base_url = cfg.OLLAMA_URL.rstrip('/')
        self._model = cfg.OLLAMA_LLM_MODEL
        self._process: asyncio.subprocess.Process | None = None
        self.state = OllamaState(model=self._model)

    def _set(self, status: OllamaStatus, detail: str | None = None) -> None:
        self.state = OllamaState(status=status, detail=detail, model=self._model)
        suffix = f' — {detail}' if detail else ''
        logger.info('Ollama runtime: %s%s', status.value, suffix)

    async def start(self) -> None:
        """Run the bring-up pipeline; never raises — failures land in self.state."""
        try:
            if not await self._is_alive():
                self._set(OllamaStatus.STARTING_SERVER)
                if not await self._spawn_serve():
                    return
            self._set(OllamaStatus.CHECKING_MODEL)
            available = await self._list_models()
            if not self._has_model(available):
                self._set(OllamaStatus.MODEL_MISSING, f'ollama pull {self._model}')
                return
            self._set(OllamaStatus.WARMING_UP)
            try:
                await self._client.generate(prompt='')
            except OllamaError as err:
                logger.warning('Ollama warmup failed (continuing): %s', err)
            self._set(OllamaStatus.READY)
        except Exception as err:
            logger.exception('Ollama runtime startup failed')
            self._set(OllamaStatus.ERROR, str(err) or type(err).__name__)

    async def stop(self) -> None:
        """Terminate ollama serve only if we spawned it; no-op otherwise."""
        proc = self._process
        if proc is None or proc.returncode is not None:
            self._process = None
            return
        self._process = None
        proc.terminate()
        try:
            await asyncio.wait_for(proc.wait(), timeout=self._STOP_TIMEOUT)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()

    async def _is_alive(self) -> bool:
        try:
            async with httpx.AsyncClient(base_url=self._base_url, timeout=self._PROBE_TIMEOUT) as c:
                response = await c.get('/api/tags')
                return response.status_code < 500
        except httpx.HTTPError:
            return False

    async def _spawn_serve(self) -> bool:
        binary = shutil.which('ollama')
        if binary is None:
            self._set(
                OllamaStatus.ERROR,
                'ollama binary not found in PATH; install from https://ollama.com/download',
            )
            return False
        try:
            self._process = await asyncio.create_subprocess_exec(
                binary,
                'serve',
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
        except OSError as err:
            self._set(OllamaStatus.ERROR, f'failed to spawn ollama serve: {err}')
            return False
        loop = asyncio.get_running_loop()
        deadline = loop.time() + self._SPAWN_WAIT_TIMEOUT
        while loop.time() < deadline:
            if self._process.returncode is not None:
                self._set(
                    OllamaStatus.ERROR,
                    f'ollama serve exited prematurely (code {self._process.returncode})',
                )
                return False
            if await self._is_alive():
                return True
            await asyncio.sleep(self._SPAWN_POLL_INTERVAL)
        self._set(
            OllamaStatus.ERROR,
            f'ollama serve did not respond within {self._SPAWN_WAIT_TIMEOUT:.0f}s',
        )
        return False

    async def _list_models(self) -> list[str]:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=self._TAGS_TIMEOUT) as c:
            response = await c.get('/api/tags')
            response.raise_for_status()
            data = response.json()
        return [item.get('name', '') for item in data.get('models', [])]

    def _has_model(self, available: list[str]) -> bool:
        target = self._model
        candidates = {target} if ':' in target else {target, f'{target}:latest'}
        return any(name in candidates for name in available)
