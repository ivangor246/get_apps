from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from .events import JobEvent

if TYPE_CHECKING:
    from .manager import JobManager


class JobHandle:
    """Passed into a job coroutine so it can emit logs and progress."""

    def __init__(self, manager: JobManager, job_id: str) -> None:
        self._manager = manager
        self.job_id = job_id

    def log(self, message: str) -> None:
        """Append a free-form log line to the job's stream."""
        self._manager._emit(self.job_id, JobEvent('log', {'message': message}))

    def progress(self, current: int, total: int | None = None) -> None:
        """Update the job's progress counters and broadcast a progress event."""
        job = self._manager._jobs.get(self.job_id)
        if job is None:
            return
        job.progress_current = current
        if total is not None:
            job.progress_total = total
        self._manager._emit(
            self.job_id,
            JobEvent('progress', {'current': current, 'total': job.progress_total}),
        )


JobCoroFactory = Callable[[JobHandle], Awaitable[Any]]


class _HandleLogBridge(logging.Handler):
    """Forward logging records from `app.*` loggers to a JobHandle."""

    def __init__(self, handle: JobHandle) -> None:
        super().__init__(level=logging.INFO)
        self._handle = handle
        self.setFormatter(logging.Formatter('%(levelname)s %(name)s — %(message)s'))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._handle.log(self.format(record))
        except Exception:  # noqa: BLE001
            pass


@contextmanager
def capture_app_logs(handle: JobHandle):
    """Temporarily route ``app.*`` log records into the given JobHandle."""
    root = logging.getLogger('app')
    bridge = _HandleLogBridge(handle)
    prev_level = root.level
    if prev_level == logging.NOTSET or prev_level > logging.INFO:
        root.setLevel(logging.INFO)
    root.addHandler(bridge)
    try:
        yield
    finally:
        root.removeHandler(bridge)
        root.setLevel(prev_level)
