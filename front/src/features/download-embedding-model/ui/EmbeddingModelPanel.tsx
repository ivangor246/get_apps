import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import { useQueryClient } from '@tanstack/react-query';
import { useStartJob } from '../../../entities/job';
import {
  SYSTEM_STATUS_KEY,
  useSystemStatus,
  type EmbeddingStatus,
} from '../../../entities/system-status';

interface Props {
  onStarted: (jobId: string) => void;
}

const STATUS_CHIP: Record<EmbeddingStatus, { label: string; color: 'success' | 'warning' | 'error' }> = {
  ready: { label: 'downloaded', color: 'success' },
  downloading: { label: 'downloading…', color: 'warning' },
  missing: { label: 'not downloaded', color: 'error' },
};

/** Shows the embedding model state and starts its download as a background job. */
export function EmbeddingModelPanel({ onStarted }: Props) {
  const qc = useQueryClient();
  const statusQ = useSystemStatus();
  const start = useStartJob<void>('/embedding/model/download');
  const embedding = statusQ.data?.embedding;

  return (
    <Box sx={{ mb: 4 }}>
      <Box sx={{ typography: 'overline', color: 'text.secondary', mb: 1 }}>Embedding Model</Box>

      {embedding ? (
        <>
          <Stack direction="row" spacing={2} sx={{ alignItems: 'center', mb: 1 }}>
            <Typography>{embedding.model}</Typography>
            <Chip
              size="small"
              label={STATUS_CHIP[embedding.status].label}
              color={STATUS_CHIP[embedding.status].color}
            />
            <Button
              variant="contained"
              disabled={embedding.status !== 'missing' || start.isPending}
              onClick={() =>
                start.mutate(undefined, {
                  onSuccess: (r) => {
                    qc.invalidateQueries({ queryKey: SYSTEM_STATUS_KEY });
                    onStarted(r.job_id);
                  },
                })
              }
            >
              {start.isPending ? 'Starting…' : 'Download'}
            </Button>
          </Stack>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
            Required for indexing and queries. Stored in <code>saved_data/cache</code>.
          </Typography>
        </>
      ) : null}

      {start.error ? (
        <Alert severity="error" sx={{ mt: 2 }}>
          Failed to start download: {String(start.error)}
        </Alert>
      ) : null}
    </Box>
  );
}
