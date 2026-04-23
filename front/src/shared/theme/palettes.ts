import { createTheme, type Theme } from '@mui/material/styles';

export type ThemeMode = 'light' | 'dark';

export function buildTheme(mode: ThemeMode): Theme {
  return createTheme({
    palette: {
      mode,
      primary: { main: mode === 'light' ? '#6750a4' : '#d0bcff' },
      secondary: { main: mode === 'light' ? '#625b71' : '#ccc2dc' },
    },
    shape: { borderRadius: 12 },
  });
}
