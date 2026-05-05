import { useQuery } from '@tanstack/react-query';
import { api } from '../../../shared/api';
import type { BackendConfig } from './types';

const CONFIG_KEY = ['config'] as const;

export function useBackendConfig() {
  return useQuery<BackendConfig>({
    queryKey: CONFIG_KEY,
    queryFn: () => api.get<BackendConfig>('/config'),
    staleTime: Infinity,
  });
}
