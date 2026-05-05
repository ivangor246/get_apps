import { useMutation } from '@tanstack/react-query';
import { api } from '../../../shared/api';
import type { JobCreated } from './types';

type StartJobParams = Record<string, string | number | boolean | null | undefined>;

export function useStartJob<TBody>(path: string, params?: StartJobParams) {
  return useMutation<JobCreated, Error, TBody>({
    mutationFn: (body) => api.post<JobCreated>(path, body, params ? { params } : undefined),
  });
}

export async function cancelJob(jobId: string): Promise<void> {
  await api.post<{ cancelled: boolean }>(`/tasks/${jobId}/cancel`);
}
