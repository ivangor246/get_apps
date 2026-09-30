export type OllamaStatus =
  | 'pending'
  | 'starting_server'
  | 'checking_model'
  | 'model_missing'
  | 'warming_up'
  | 'ready'
  | 'error';

export interface OllamaStatusInfo {
  status: OllamaStatus;
  detail: string | null;
  model: string | null;
}

export type EmbeddingStatus = 'ready' | 'missing' | 'downloading';

export interface EmbeddingStatusInfo {
  status: EmbeddingStatus;
  detail: string | null;
  model: string;
}

export interface SystemStatus {
  backend: string;
  ollama: OllamaStatusInfo;
  embedding: EmbeddingStatusInfo;
}
