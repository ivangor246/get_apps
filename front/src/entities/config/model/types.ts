export interface AppConfig {
  OLLAMA_URL: string;
  OLLAMA_LLM_MODEL: string;
  OLLAMA_TIMEOUT: number;
  EMBEDDING_MODEL: string;
  EMBEDDING_DEVICE: string;
  EMBEDDING_DIM: number;
  EMBEDDING_BATCH_SIZE: number;
  EMBEDDING_GPU_MEM_LIMIT_MB: number;
  RAG_TOP_K: number;
  RAG_CANDIDATE_K: number;
  API_HOST: string;
  API_PORT: number;
}

export type AppConfigPatch = Partial<AppConfig>;
