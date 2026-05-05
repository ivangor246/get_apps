export interface TunableConfig {
  OLLAMA_LLM_MODEL: string;
  OLLAMA_TIMEOUT: number;
  OLLAMA_CONTEXT_SIZE: number;
  RAG_TOP_K: number;
  RAG_CANDIDATE_K: number;
  EMBEDDING_BATCH_SIZE: number;
}

export interface ReadOnlyConfig {
  OLLAMA_URL: string;
  EMBEDDING_MODEL: string;
  EMBEDDING_DIM: number;
}

export interface BackendConfig {
  tunable: TunableConfig;
  read_only: ReadOnlyConfig;
}

export type ConfigOverrides = Partial<TunableConfig>;
