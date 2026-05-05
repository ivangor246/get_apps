import asyncio
import time
import uuid
from collections.abc import AsyncIterator

from .events import JobEvent
from .handle import JobCoroFactory, JobHandle, capture_app_logs
from .job import Job


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
            with capture_app_logs(handle):
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
