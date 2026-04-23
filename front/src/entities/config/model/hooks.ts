import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../../shared/api';
import type { AppConfig, AppConfigPatch } from './types';

const CONFIG_KEY = ['config'] as const;
const DEFAULTS_KEY = ['config', 'defaults'] as const;

export function useConfig() {
  return useQuery<AppConfig>({
    queryKey: CONFIG_KEY,
    queryFn: () => api.get<AppConfig>('/config'),
  });
}

export function useConfigDefaults() {
  return useQuery<AppConfig>({
    queryKey: DEFAULTS_KEY,
    queryFn: () => api.get<AppConfig>('/config/defaults'),
    staleTime: Infinity,
  });
}

export function useUpdateConfig() {
  const qc = useQueryClient();
  return useMutation<AppConfig, Error, AppConfigPatch>({
    mutationFn: (patch) => api.put<AppConfig>('/config', patch),
    onSuccess: (data) => {
      qc.setQueryData(CONFIG_KEY, data);
    },
  });
}
