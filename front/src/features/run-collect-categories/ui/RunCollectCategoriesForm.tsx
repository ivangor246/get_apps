import { useState } from 'react';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import { useStartJob } from '../../../entities/job';

interface Body {
  concurrency: number;
}

interface Props {
  onStarted: (jobId: string) => void;
}

export function RunCollectCategoriesForm({ onStarted }: Props) {
  const [concurrency, setConcurrency] = useState(3);
  const start = useStartJob<Body>('/tasks/collect-categories');

  return (
    <Stack spacing={2} sx={{ maxWidth: 360 }}>
      <TextField
        type="number"
        label="Concurrency"
        value={concurrency}
        onChange={(e) => setConcurrency(Math.max(1, Number(e.target.value) || 1))}
      />
      <Button
        variant="contained"
        disabled={start.isPending}
        onClick={() => start.mutate({ concurrency }, { onSuccess: (r) => onStarted(r.job_id) })}
      >
        {start.isPending ? 'Starting…' : 'Collect categories'}
      </Button>
    </Stack>
  );
}
