export interface OllamaModelInfo {
  name: string;
  downloaded: boolean;
  loaded: boolean;
}

export interface OllamaModelsResponse {
  current: string;
  models: OllamaModelInfo[];
}
