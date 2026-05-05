import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';
import { ConfigForm } from '../../../features/edit-config';
import { ToggleThemeButton } from '../../../features/toggle-theme';
import { ModelPicker } from '../../../widgets/model-picker';

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

      <ModelPicker />

      <Divider sx={{ mb: 4 }} />

      <Typography variant="h6" gutterBottom>
        Runtime configuration
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Tunable settings live in your browser (localStorage) and travel with each request as query
        parameters. Read-only fields show backend defaults — change them in{' '}
        <code>back/src/app/core/config.py</code> and restart the backend.
      </Typography>

      <ConfigForm />
    </>
  );
}
