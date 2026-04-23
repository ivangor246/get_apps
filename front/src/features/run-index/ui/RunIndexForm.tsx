import { useState } from 'react';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import { DbSelector } from '../../../widgets/db-selector';
import { useStartJob } from '../../../entities/job';

interface Body {
  db_name: string;
  batch_size: number;
  concurrency: number;
}

interface Props {
  onStarted: (jobId: string) => void;
}

export function RunIndexForm({ onStarted }: Props) {
  const [dbName, setDbName] = useState('');
  const [batchSize, setBatchSize] = useState(32);
  const [concurrency, setConcurrency] = useState(1);
  const start = useStartJob<Body>('/tasks/index');

  return (
    <Stack spacing={2} sx={{ maxWidth: 560 }}>
      <DbSelector value={dbName} onChange={setDbName} />

      <Stack direction="row" spacing={2}>
        <TextField
          type="number"
          label="Batch size"
          value={batchSize}
          onChange={(e) => setBatchSize(Math.max(1, Number(e.target.value) || 1))}
        />
        <TextField
          type="number"
          label="Concurrency"
          value={concurrency}
          onChange={(e) => setConcurrency(Math.max(1, Number(e.target.value) || 1))}
        />
      </Stack>

      <Button
        variant="contained"
        disabled={start.isPending || dbName.trim() === ''}
        onClick={() =>
          start.mutate(
            { db_name: dbName.trim(), batch_size: batchSize, concurrency },
            { onSuccess: (r) => onStarted(r.job_id) },
          )
        }
      >
        {start.isPending ? 'Starting…' : 'Start indexing'}
      </Button>
    </Stack>
  );
}
