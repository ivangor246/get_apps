from pydantic import BaseModel


class JobCreated(BaseModel):
    """Acknowledgement returned when a background job is submitted."""

    job_id: str
    kind: str


class JobSnapshot(BaseModel):
    """Point-in-time view of a background job's state and progress."""

    id: str
    kind: str
    status: str
    progress_current: int
    progress_total: int | None = None
    error: str | None = None
    created_at: float
    started_at: float | None = None
    finished_at: float | None = None
