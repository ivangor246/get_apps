import { useMutation } from '@tanstack/react-query';
import { api } from '../../../shared/api';
import { pickOverrides, useConfigOverrides } from '../../../shared/config';
import type { RAGQueryPayload, RAGResponse } from './types';

const RAG_OVERRIDE_KEYS = [
  'RAG_TOP_K',
  'RAG_CANDIDATE_K',
  'OLLAMA_LLM_MODEL',
  'OLLAMA_TIMEOUT',
  'OLLAMA_CONTEXT_SIZE',
] as const;

export function useRagQuery() {
  const { overrides } = useConfigOverrides();
  return useMutation<RAGResponse, Error, RAGQueryPayload>({
    mutationFn: (body) =>
      api.post<RAGResponse>('/rag/query', body, { params: pickOverrides(overrides, RAG_OVERRIDE_KEYS) }),
  });
}
