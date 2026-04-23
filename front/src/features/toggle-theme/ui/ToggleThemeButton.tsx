import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import LightModeIcon from '@mui/icons-material/LightMode';
import { useThemeMode } from '../../../shared/theme';

export function ToggleThemeButton() {
  const { mode, toggle } = useThemeMode();
  const next = mode === 'light' ? 'dark' : 'light';
  return (
    <Tooltip title={`Switch to ${next} theme`}>
      <IconButton onClick={toggle} color="inherit" aria-label="toggle theme">
        {mode === 'light' ? <DarkModeIcon /> : <LightModeIcon />}
      </IconButton>
    </Tooltip>
  );
}
