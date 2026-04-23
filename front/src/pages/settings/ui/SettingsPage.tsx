import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';
import { ConfigForm } from '../../../features/edit-config';
import { ToggleThemeButton } from '../../../features/toggle-theme';

export function SettingsPage() {
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

      <Typography variant="h6" gutterBottom>
        Runtime configuration
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Overrides persist to <code>saved_data/config.json</code>. A backend restart is required for
        values used at startup (embedder, Ollama client) to take effect.
      </Typography>

      <ConfigForm />
    </>
  );
}
