import { useState } from 'react';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import { DbSelector } from '../../../widgets/db-selector';
import { useStartJob } from '../../../entities/job';
import { useBackendConfig } from '../../../entities/config';
import { pickOverrides, useConfigOverrides } from '../../../shared/config';

interface Body {
  db_name: string;
  concurrency: number;
}

interface Props {
  onStarted: (jobId: string) => void;
}

const INDEX_OVERRIDE_KEYS = ['EMBEDDING_BATCH_SIZE'] as const;

export function RunIndexForm({ onStarted }: Props) {
  const [dbName, setDbName] = useState('');
  const [concurrency, setConcurrency] = useState(1);
  const configQ = useBackendConfig();
  const { overrides } = useConfigOverrides();
  const effectiveBatchSize =
    overrides.EMBEDDING_BATCH_SIZE ?? configQ.data?.tunable.EMBEDDING_BATCH_SIZE ?? 8;
  const start = useStartJob<Body>('/tasks/index', pickOverrides(overrides, INDEX_OVERRIDE_KEYS));

  return (
    <Stack spacing={2} sx={{ maxWidth: 560 }}>
      <DbSelector value={dbName} onChange={setDbName} />

      <Stack direction="row" spacing={2}>
        <TextField
          type="number"
          label="Batch size"
          value={effectiveBatchSize}
          helperText="Edit on Settings page"
          disabled
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
            { db_name: dbName.trim(), concurrency },
            { onSuccess: (r) => onStarted(r.job_id) },
          )
        }
      >
        {start.isPending ? 'Starting…' : 'Start indexing'}
      </Button>
    </Stack>
  );
}
