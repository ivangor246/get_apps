export type OllamaStatus =
  | 'pending'
  | 'starting_server'
  | 'ready'
  | 'error';

export interface OllamaStatusInfo {
  status: OllamaStatus;
  detail: string | null;
}

export interface SystemStatus {
  backend: string;
  ollama: OllamaStatusInfo;
}
