import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import { NavLink } from 'react-router-dom';
import { ToggleThemeButton } from '../../../features/toggle-theme';
import { StatusIndicator } from './StatusIndicator';

const links: Array<{ to: string; label: string }> = [
  { to: '/', label: 'Query' },
  { to: '/collection', label: 'Collection' },
  { to: '/indexing', label: 'Indexing' },
  { to: '/settings', label: 'Settings' },
];

export function AppHeader() {
  return (
    <AppBar position="sticky" color="default" elevation={1}>
      <Toolbar>
        <Typography variant="h6" sx={{ mr: 4, fontWeight: 600 }}>
          get_apps
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, flexGrow: 1 }}>
          {links.map((l) => (
            <Button
              key={l.to}
              component={NavLink}
              to={l.to}
              end={l.to === '/'}
              color="inherit"
              sx={{
                '&.active': {
                  color: 'primary.main',
                  fontWeight: 600,
                },
              }}
            >
              {l.label}
            </Button>
          ))}
        </Box>
        <StatusIndicator />
        <ToggleThemeButton />
      </Toolbar>
    </AppBar>
  );
}
