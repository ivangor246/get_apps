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

export interface SystemStatus {
  backend: string;
  ollama: OllamaStatusInfo;
}
