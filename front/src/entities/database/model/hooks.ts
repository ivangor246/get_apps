import { useQuery } from '@tanstack/react-query';
import { api } from '../../../shared/api';

export function useDatabases() {
  return useQuery<string[]>({
    queryKey: ['databases'],
    queryFn: async () => (await api.get<{ databases: string[] }>('/databases')).databases,
  });
}

export function useCategoriesRuns() {
  return useQuery<string[]>({
    queryKey: ['categories-runs'],
    queryFn: async () => (await api.get<{ runs: string[] }>('/categories-runs')).runs,
  });
}
