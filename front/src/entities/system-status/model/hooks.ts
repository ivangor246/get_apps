import { useQuery } from '@tanstack/react-query';
import { api } from '../../../shared/api';
import type { SystemStatus } from './types';

const STATUS_KEY = ['system-status'] as const;

const FAST_POLL_MS = 2000;
const SLOW_POLL_MS = 30000;

export function useSystemStatus() {
  return useQuery<SystemStatus>({
    queryKey: STATUS_KEY,
    queryFn: () => api.get<SystemStatus>('/status'),
    refetchInterval: (query) => {
      if (query.state.error) return FAST_POLL_MS;
      const data = query.state.data;
      return data?.ollama.status === 'ready' ? SLOW_POLL_MS : FAST_POLL_MS;
    },
    refetchIntervalInBackground: true,
    retry: false,
  });
}
