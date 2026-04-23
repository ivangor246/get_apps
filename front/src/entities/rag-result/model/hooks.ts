import { useMutation } from '@tanstack/react-query';
import { api } from '../../../shared/api';
import type { RAGQueryPayload, RAGResponse } from './types';

export function useRagQuery() {
  return useMutation<RAGResponse, Error, RAGQueryPayload>({
    mutationFn: (body) => api.post<RAGResponse>('/rag/query', body),
  });
}
