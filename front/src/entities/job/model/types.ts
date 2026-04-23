export type JobStatus = 'pending' | 'running' | 'done' | 'error' | 'cancelled';

export interface JobCreated {
  job_id: string;
  kind: string;
}

export interface JobSnapshot {
  id: string;
  kind: string;
  status: JobStatus;
  progress_current: number;
  progress_total: number | null;
  error: string | null;
  created_at: number;
  started_at: number | null;
  finished_at: number | null;
}
