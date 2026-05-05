export interface OllamaModelInfo {
  name: string;
  downloaded: boolean;
  loaded: boolean;
}

export interface OllamaModelsResponse {
  models: OllamaModelInfo[];
}
