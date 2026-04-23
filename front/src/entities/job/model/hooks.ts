import { useMutation } from '@tanstack/react-query';
import { api } from '../../../shared/api';
import type { JobCreated } from './types';

export function useStartJob<TBody>(path: string) {
  return useMutation<JobCreated, Error, TBody>({
    mutationFn: (body) => api.post<JobCreated>(path, body),
  });
}

export async function cancelJob(jobId: string): Promise<void> {
  await api.post<{ cancelled: boolean }>(`/tasks/${jobId}/cancel`);
}
