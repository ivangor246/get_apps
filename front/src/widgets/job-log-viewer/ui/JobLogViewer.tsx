import { useEffect, useRef, useState } from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import { openSse, type SseEvent } from '../../../shared/api';
import { cancelJob, type JobStatus } from '../../../entities/job';

interface Props {
  jobId: string;
  onClose?: () => void;
}

interface LogLine {
  id: number;
  text: string;
}

const statusColor: Record<JobStatus, 'default' | 'info' | 'success' | 'error' | 'warning'> = {
  pending: 'default',
  running: 'info',
  done: 'success',
  error: 'error',
  cancelled: 'warning',
};

export function JobLogViewer({ jobId, onClose }: Props) {
  const [logs, setLogs] = useState<LogLine[]>([]);
  const [status, setStatus] = useState<JobStatus>('pending');
  const [current, setCurrent] = useState(0);
  const [total, setTotal] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const logRef = useRef<HTMLDivElement>(null);
  const counter = useRef(0);

  useEffect(() => {
    setLogs([]);
    setStatus('pending');
    setCurrent(0);
    setTotal(null);
    setError(null);

    const close = openSse(`/tasks/${jobId}/events`, (ev: SseEvent) => {
      if (ev.type === 'log') {
        counter.current += 1;
        setLogs((prev) => [
          ...prev.slice(-499),
          { id: counter.current, text: String(ev.message ?? '') },
        ]);
      } else if (ev.type === 'progress') {
        if (typeof ev.current === 'number') setCurrent(ev.current);
        if (typeof ev.total === 'number') setTotal(ev.total);
      } else if (ev.type === 'status') {
        if (ev.status) setStatus(ev.status as JobStatus);
      } else if (ev.type === 'done') {
        setStatus('done');
      } else if (ev.type === 'error') {
        setStatus((ev.status as JobStatus) ?? 'error');
        if (typeof ev.message === 'string') setError(ev.message);
      }
    });
    return close;
  }, [jobId]);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [logs]);

  const pct = total ? Math.min(100, (current / total) * 100) : null;
  const active = status === 'pending' || status === 'running';

  return (
    <Box sx={{ border: 1, borderColor: 'divider', borderRadius: 2, p: 2 }}>
      <Stack direction="row" spacing={2} sx={{ alignItems: 'center', mb: 2 }}>
        <Typography variant="subtitle2" sx={{ fontFamily: 'monospace' }}>
          job {jobId.slice(0, 8)}
        </Typography>
        <Chip size="small" label={status} color={statusColor[status]} />
        {total !== null ? (
          <Typography variant="caption" color="text.secondary">
            {current} / {total}
          </Typography>
        ) : null}
        <Box sx={{ flexGrow: 1 }} />
        {active ? (
          <Button size="small" color="warning" onClick={() => cancelJob(jobId)}>
            Cancel
          </Button>
        ) : null}
        {onClose ? (
          <Button size="small" onClick={onClose}>
            Close
          </Button>
        ) : null}
      </Stack>

      {active ? (
        <LinearProgress
          variant={pct === null ? 'indeterminate' : 'determinate'}
          value={pct ?? undefined}
          sx={{ mb: 2 }}
        />
      ) : null}

      {error ? (
        <Typography color="error" variant="body2" sx={{ mb: 1 }}>
          {error}
        </Typography>
      ) : null}

      <Box
        ref={logRef}
        sx={{
          fontFamily: 'monospace',
          fontSize: 13,
          whiteSpace: 'pre-wrap',
          maxHeight: 360,
          overflow: 'auto',
          bgcolor: 'action.hover',
          borderRadius: 1,
          p: 1.5,
        }}
      >
        {logs.length === 0 ? (
          <Typography variant="caption" color="text.secondary">
            Waiting for logs…
          </Typography>
        ) : (
          logs.map((l) => <div key={l.id}>{l.text}</div>)
        )}
      </Box>
    </Box>
  );
}
