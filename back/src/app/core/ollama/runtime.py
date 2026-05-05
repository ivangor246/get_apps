from __future__ import annotations

import asyncio
import logging
import shutil
from dataclasses import dataclass
from enum import Enum

import httpx

from ..config import get_config
from .client import OllamaClient

logger = logging.getLogger('app')


class OllamaStatus(str, Enum):
    """Lifecycle states of the local Ollama bring-up pipeline."""

    PENDING = 'pending'
    STARTING_SERVER = 'starting_server'
    READY = 'ready'
    ERROR = 'error'


@dataclass
class OllamaState:
    """Snapshot of the runtime: current status plus a human-readable detail."""

    status: OllamaStatus = OllamaStatus.PENDING
    detail: str | None = None


class OllamaRuntime:
    """Spawns ollama serve if needed and reports readiness; the model is chosen per request."""

    _PROBE_TIMEOUT = 1.0
    _SPAWN_WAIT_TIMEOUT = 15.0
    _SPAWN_POLL_INTERVAL = 0.5
    _STOP_TIMEOUT = 5.0

    def __init__(self, client: OllamaClient) -> None:
        cfg = get_config()
        self._client = client
        self._base_url = cfg.OLLAMA_URL.rstrip('/')
        self._process: asyncio.subprocess.Process | None = None
        self.state = OllamaState()

    def _set(self, status: OllamaStatus, detail: str | None = None) -> None:
        self.state = OllamaState(status=status, detail=detail)
        suffix = f' — {detail}' if detail else ''
        logger.info('Ollama runtime: %s%s', status.value, suffix)

    async def start(self) -> None:
        """Run the bring-up pipeline; never raises — failures land in self.state."""
        try:
            if not await self._is_alive():
                self._set(OllamaStatus.STARTING_SERVER)
                if not await self._spawn_serve():
                    return
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
