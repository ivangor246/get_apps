import { useState } from 'react';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';
import { EmbeddingModelPanel } from '../../../features/download-embedding-model';
import { ConfigForm } from '../../../features/edit-config';
import { ToggleThemeButton } from '../../../features/toggle-theme';
import { JobLogViewer } from '../../../widgets/job-log-viewer';
import { ModelPicker } from '../../../widgets/model-picker';

export function SettingsPage() {
  const [downloadJobId, setDownloadJobId] = useState<string | null>(null);

  return (
    <>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Typography variant="subtitle1">Theme</Typography>
        <ToggleThemeButton />
      </Box>

      <Divider sx={{ mb: 4 }} />

      <ModelPicker />

      <Divider sx={{ mb: 4 }} />

      <EmbeddingModelPanel onStarted={setDownloadJobId} />
      {downloadJobId ? (
        <Box sx={{ mb: 4 }}>
          <JobLogViewer jobId={downloadJobId} onClose={() => setDownloadJobId(null)} />
        </Box>
      ) : null}

      <Divider sx={{ mb: 4 }} />

      <Typography variant="h6" gutterBottom>
        Runtime configuration
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Overrides persist to <code>saved_data/config.json</code>. A backend restart is required for
        values used at startup (embedder, Ollama URL) to take effect.
      </Typography>

      <ConfigForm />
    </>
  );
}
