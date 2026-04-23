import { useState } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { RunIndexForm } from '../../../features/run-index';
import { JobLogViewer } from '../../../widgets/job-log-viewer';

export function IndexingPage() {
  const [jobId, setJobId] = useState<string | null>(null);

  return (
    <>
      <Typography variant="h4" gutterBottom>
        Indexing
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Embeds every app description in the selected database and writes vectors to Chroma.
      </Typography>

      <RunIndexForm onStarted={setJobId} />

      {jobId ? (
        <Box sx={{ mt: 4 }}>
          <JobLogViewer jobId={jobId} onClose={() => setJobId(null)} />
        </Box>
      ) : null}
    </>
  );
}
