import { useState } from 'react';
import Button from '@mui/material/Button';
import MenuItem from '@mui/material/MenuItem';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import { DbSelector } from '../../../widgets/db-selector';
import { useCategoriesRuns } from '../../../entities/database';
import { useStartJob } from '../../../entities/job';

interface Body {
  db_name: string;
  folder_name: string | null;
  concurrency: number;
}

interface Props {
  onStarted: (jobId: string) => void;
}

export function RunCollectAppsForm({ onStarted }: Props) {
  const [dbName, setDbName] = useState('');
  const [folder, setFolder] = useState('');
  const [concurrency, setConcurrency] = useState(3);
  const runs = useCategoriesRuns();
  const start = useStartJob<Body>('/tasks/collect-apps');

  return (
    <Stack spacing={2} sx={{ maxWidth: 560 }}>
      <DbSelector value={dbName} onChange={setDbName} allowNew />

      <TextField
        select
        label="Categories run"
        value={folder}
        onChange={(e) => setFolder(e.target.value)}
        helperText={runs.isLoading ? 'Loading…' : 'Defaults to the most recent run'}
        sx={{ maxWidth: 320 }}
      >
        <MenuItem value="">
          <em>latest</em>
        </MenuItem>
        {(runs.data ?? []).map((r) => (
          <MenuItem key={r} value={r}>
            {r}
          </MenuItem>
        ))}
      </TextField>

      <TextField
        type="number"
        label="Concurrency"
        value={concurrency}
        onChange={(e) => setConcurrency(Math.max(1, Number(e.target.value) || 1))}
        sx={{ maxWidth: 200 }}
      />

      <Button
        variant="contained"
        disabled={start.isPending || dbName.trim() === ''}
        onClick={() =>
          start.mutate(
            {
              db_name: dbName.trim(),
              folder_name: folder === '' ? null : folder,
              concurrency,
            },
            { onSuccess: (r) => onStarted(r.job_id) },
          )
        }
      >
        {start.isPending ? 'Starting…' : 'Collect apps'}
      </Button>
    </Stack>
  );
}
