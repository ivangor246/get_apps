import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from .events import LOG_BUFFER_SIZE, JobEvent, JobStatus


@dataclass
class Job:
    """Tracked background job: identity, lifecycle state, log buffer, live subscribers."""

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
        """Serializable view of the job's persistent fields (no logs/subscribers/task)."""
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
