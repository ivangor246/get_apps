import asyncio
import json
import logging
import time
import uuid
from collections import deque
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Literal

JobStatus = Literal['pending', 'running', 'done', 'error', 'cancelled']
EventType = Literal['log', 'progress', 'status', 'done', 'error']

LOG_BUFFER_SIZE = 500


@dataclass
class JobEvent:
    type: EventType
    data: dict[str, Any]
    ts: float = field(default_factory=time.time)

    def to_sse(self) -> str:
        payload = {'type': self.type, 'ts': self.ts, **self.data}
        return f'event: {self.type}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n'


@dataclass
class Job:
    id: str
    kind: str
    status: JobStatus = 'pending'
    progress_current: int = 0
    progress_total: int | None = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    finished_at: float | None = None
    logs: deque[JobEvent] = field(default_factory=lambda: deque(maxlen=LOG_BUFFER_SIZE))
    subscribers: list[asyncio.Queue[JobEvent | None]] = field(default_factory=list)
    task: asyncio.Task | None = None

    def snapshot(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'kind': self.kind,
            'status': self.status,
            'progress_current': self.progress_current,
            'progress_total': self.progress_total,
            'error': self.error,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'finished_at': self.finished_at,
        }


class JobHandle:
    """Passed into a job coroutine so it can emit logs and progress."""

    def __init__(self, manager: 'JobManager', job_id: str) -> None:
        self._manager = manager
        self.job_id = job_id

    def log(self, message: str) -> None:
        self._manager._emit(self.job_id, JobEvent('log', {'message': message}))

    def progress(self, current: int, total: int | None = None) -> None:
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

    def __init__(self, handle: 'JobHandle') -> None:
        super().__init__(level=logging.INFO)
        self._handle = handle
        self.setFormatter(logging.Formatter('%(levelname)s %(name)s — %(message)s'))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._handle.log(self.format(record))
        except Exception:  # noqa: BLE001
            pass


@contextmanager
def _capture_app_logs(handle: 'JobHandle'):
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


class JobManager:
    """In-memory registry of async jobs with per-job log buffer and SSE subscribers."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def submit(self, kind: str, coro_factory: JobCoroFactory) -> Job:
        """Schedule a coroutine as a tracked job; returns the Job immediately."""
        job = Job(id=uuid.uuid4().hex, kind=kind)
        self._jobs[job.id] = job
        handle = JobHandle(self, job.id)
        job.task = asyncio.create_task(self._run(job, coro_factory, handle))
        return job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def cancel(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job is None or job.task is None or job.task.done():
            return False
        job.task.cancel()
        return True

    async def subscribe(self, job_id: str) -> AsyncIterator[JobEvent]:
        """Yield buffered events then live ones until the job ends and the queue closes."""
        job = self._jobs.get(job_id)
        if job is None:
            return
        queue: asyncio.Queue[JobEvent | None] = asyncio.Queue()
        for ev in list(job.logs):
            yield ev
        yield JobEvent('status', job.snapshot())
        if job.status in ('done', 'error', 'cancelled'):
            return
        job.subscribers.append(queue)
        try:
            while True:
                ev = await queue.get()
                if ev is None:
                    return
                yield ev
        finally:
            if queue in job.subscribers:
                job.subscribers.remove(queue)

    def _emit(self, job_id: str, event: JobEvent) -> None:
        job = self._jobs.get(job_id)
        if job is None:
            return
        job.logs.append(event)
        for q in job.subscribers:
            q.put_nowait(event)

    async def _run(self, job: Job, coro_factory: JobCoroFactory, handle: JobHandle) -> None:
        job.status = 'running'
        job.started_at = time.time()
        self._emit(job.id, JobEvent('status', job.snapshot()))
        try:
            with _capture_app_logs(handle):
                await coro_factory(handle)
            job.status = 'done'
            self._emit(job.id, JobEvent('done', job.snapshot()))
        except asyncio.CancelledError:
            job.status = 'cancelled'
            self._emit(job.id, JobEvent('error', {'message': 'cancelled', **job.snapshot()}))
            raise
        except Exception as exc:  # noqa: BLE001
            job.status = 'error'
            job.error = f'{type(exc).__name__}: {exc}'
            self._emit(job.id, JobEvent('error', {'message': job.error, **job.snapshot()}))
        finally:
            job.finished_at = time.time()
            for q in job.subscribers:
                q.put_nowait(None)

    async def sse_stream(self, job_id: str) -> AsyncIterator[str]:
        """SSE-formatted text stream of events for a job; ends when the job finishes."""
        async for event in self.subscribe(job_id):
            yield event.to_sse()
