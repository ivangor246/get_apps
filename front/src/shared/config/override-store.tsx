import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import type { ConfigOverrides, TunableConfig } from '../../entities/config';

interface ConfigOverridesContextValue {
  overrides: ConfigOverrides;
  setOverride: <K extends keyof TunableConfig>(key: K, value: TunableConfig[K] | undefined) => void;
  resetAll: () => void;
}

const ConfigOverridesContext = createContext<ConfigOverridesContextValue | null>(null);

const STORAGE_KEY = 'get_apps.config-overrides';

function readInitialOverrides(): ConfigOverrides {
  if (typeof window === 'undefined') return {};
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === 'object' ? (parsed as ConfigOverrides) : {};
  } catch {
    return {};
  }
}

export function ConfigOverridesProvider({ children }: { children: ReactNode }) {
  const [overrides, setOverrides] = useState<ConfigOverrides>(readInitialOverrides);

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(overrides));
  }, [overrides]);

  const setOverride = useCallback(
    <K extends keyof TunableConfig>(key: K, value: TunableConfig[K] | undefined) => {
      setOverrides((prev) => {
        const next = { ...prev };
        if (value === undefined) {
          delete next[key];
        } else {
          next[key] = value;
        }
        return next;
      });
    },
    [],
  );

  const resetAll = useCallback(() => setOverrides({}), []);

  const value = useMemo<ConfigOverridesContextValue>(
    () => ({ overrides, setOverride, resetAll }),
    [overrides, setOverride, resetAll],
  );

  return <ConfigOverridesContext.Provider value={value}>{children}</ConfigOverridesContext.Provider>;
}

export function useConfigOverrides(): ConfigOverridesContextValue {
  const ctx = useContext(ConfigOverridesContext);
  if (!ctx) throw new Error('useConfigOverrides must be used within ConfigOverridesProvider');
  return ctx;
}

const PARAM_NAMES: Record<keyof TunableConfig, string> = {
  OLLAMA_LLM_MODEL: 'llm_model',
  OLLAMA_TIMEOUT: 'ollama_timeout',
  OLLAMA_CONTEXT_SIZE: 'ollama_context_size',
  RAG_TOP_K: 'top_k',
  RAG_CANDIDATE_K: 'candidate_k',
  EMBEDDING_BATCH_SIZE: 'batch_size',
};

export function pickOverrides<K extends keyof TunableConfig>(
  overrides: ConfigOverrides,
  keys: readonly K[],
): Record<string, string | number> {
  const result: Record<string, string | number> = {};
  for (const key of keys) {
    const value = overrides[key];
    if (value !== undefined) {
      result[PARAM_NAMES[key]] = value;
    }
  }
  return result;
}
