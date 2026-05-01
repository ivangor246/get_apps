import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../../shared/api';
import type { OllamaModelsResponse } from './types';

export const OLLAMA_MODELS_KEY = ['ollama', 'models'] as const;

export function useOllamaModels() {
  return useQuery<OllamaModelsResponse>({
    queryKey: OLLAMA_MODELS_KEY,
    queryFn: () => api.get<OllamaModelsResponse>('/ollama/models'),
    refetchOnWindowFocus: false,
  });
}

export function useLoadOllamaModel() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: (model) => api.post<void>('/ollama/models/load', { model }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: OLLAMA_MODELS_KEY });
    },
  });
}
