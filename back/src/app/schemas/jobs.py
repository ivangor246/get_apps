from pydantic import BaseModel


class JobCreated(BaseModel):
    job_id: str
    kind: str


class JobSnapshot(BaseModel):
    id: str
    kind: str
    status: str
    progress_current: int
    progress_total: int | None = None
    error: str | None = None
    created_at: float
    started_at: float | None = None
    finished_at: float | None = None
