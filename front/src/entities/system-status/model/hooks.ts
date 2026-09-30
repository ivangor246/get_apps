import { useQuery } from '@tanstack/react-query';
import { api } from '../../../shared/api';
import type { SystemStatus } from './types';

export const SYSTEM_STATUS_KEY = ['system-status'] as const;

const FAST_POLL_MS = 2000;
const SLOW_POLL_MS = 30000;

export function useSystemStatus() {
  return useQuery<SystemStatus>({
    queryKey: SYSTEM_STATUS_KEY,
    queryFn: () => api.get<SystemStatus>('/status'),
    refetchInterval: (query) => {
      if (query.state.error) return FAST_POLL_MS;
      const data = query.state.data;
      const settled = data?.ollama.status === 'ready' && data.embedding.status !== 'downloading';
      return settled ? SLOW_POLL_MS : FAST_POLL_MS;
    },
    refetchIntervalInBackground: true,
    retry: false,
  });
}
