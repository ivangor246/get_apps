import { useState } from 'react';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';
import { RunCollectCategoriesForm } from '../../../features/run-collect-categories';
import { RunCollectAppsForm } from '../../../features/run-collect-apps';
import { JobLogViewer } from '../../../widgets/job-log-viewer';

export function CollectionPage() {
  const [jobId, setJobId] = useState<string | null>(null);

  return (
    <>
      <Typography variant="h4" gutterBottom>
        Collection
      </Typography>

      <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>
        1. Collect categories
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        Crawls the RuStore catalogue and saves app IDs per category into a new timestamped folder.
      </Typography>
      <RunCollectCategoriesForm onStarted={setJobId} />

      <Divider sx={{ my: 4 }} />

      <Typography variant="h6" sx={{ mb: 1 }}>
        2. Collect app details
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 2 }}>
        Fetches full metadata for each app ID from the chosen run and stores it in a SQLite database.
      </Typography>
      <RunCollectAppsForm onStarted={setJobId} />

      {jobId ? (
        <Box sx={{ mt: 4 }}>
          <JobLogViewer jobId={jobId} onClose={() => setJobId(null)} />
        </Box>
      ) : null}
    </>
  );
}
