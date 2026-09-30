import { useQuery } from '@tanstack/react-query';
import { api } from '../../../shared/api';
import type { OllamaStatus, SystemStatus } from './types';

export const SYSTEM_STATUS_KEY = ['system-status'] as const;

const FAST_POLL_MS = 2000;
const SLOW_POLL_MS = 30000;

// The backend checks Ollama once at startup, so these states only change after a restart.
const OLLAMA_FINAL_STATUSES: ReadonlySet<OllamaStatus> = new Set([
  'ready',
  'model_missing',
  'error',
]);

export function useSystemStatus() {
  return useQuery<SystemStatus>({
    queryKey: SYSTEM_STATUS_KEY,
    queryFn: () => api.get<SystemStatus>('/status'),
    refetchInterval: (query) => {
      if (query.state.error) return FAST_POLL_MS;
      const data = query.state.data;
      const settled =
        data !== undefined &&
        OLLAMA_FINAL_STATUSES.has(data.ollama.status) &&
        data.embedding.status !== 'downloading';
      return settled ? SLOW_POLL_MS : FAST_POLL_MS;
    },
    refetchIntervalInBackground: true,
    retry: false,
  });
}
