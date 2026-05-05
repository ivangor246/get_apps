import type { ReactNode } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigOverridesProvider } from '../../shared/config';
import { AppThemeProvider } from '../../shared/theme';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 5_000, refetchOnWindowFocus: false, retry: 1 },
  },
});

export function withProviders(children: ReactNode) {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigOverridesProvider>
        <AppThemeProvider>
          <BrowserRouter>{children}</BrowserRouter>
        </AppThemeProvider>
      </ConfigOverridesProvider>
    </QueryClientProvider>
  );
}
