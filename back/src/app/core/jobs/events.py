import json
import time
from dataclasses import dataclass, field
from typing import Any, Literal

JobStatus = Literal['pending', 'running', 'done', 'error', 'cancelled']
EventType = Literal['log', 'progress', 'status', 'done', 'error']

LOG_BUFFER_SIZE = 500


@dataclass
class JobEvent:
    """One observable event in a job's lifetime, serializable as an SSE frame."""

    type: EventType
    data: dict[str, Any]
    ts: float = field(default_factory=time.time)

    def to_sse(self) -> str:
        """Render the event as a single ``event:``/``data:`` SSE frame."""
        payload = {'type': self.type, 'ts': self.ts, **self.data}
        return f'event: {self.type}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n'
