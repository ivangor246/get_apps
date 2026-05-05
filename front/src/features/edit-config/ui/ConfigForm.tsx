import type { ChangeEvent } from 'react';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import InputAdornment from '@mui/material/InputAdornment';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import {
  useBackendConfig,
  type ReadOnlyConfig,
  type TunableConfig,
} from '../../../entities/config';
import { useConfigOverrides } from '../../../shared/config';

type TunableSpec = {
  key: keyof TunableConfig;
  label: string;
  type: 'text' | 'number';
  group: 'Ollama' | 'RAG' | 'Embedding';
  description: string;
};

const TUNABLE_FIELDS: TunableSpec[] = [
  {
    key: 'OLLAMA_LLM_MODEL',
    label: 'LLM model',
    type: 'text',
    group: 'Ollama',
    description: 'Name of the language model used to generate answers.',
  },
  {
    key: 'OLLAMA_TIMEOUT',
    label: 'Timeout (s)',
    type: 'number',
    group: 'Ollama',
    description: 'Maximum time in seconds to wait for a model response.',
  },
  {
    key: 'OLLAMA_CONTEXT_SIZE',
    label: 'Context size',
    type: 'number',
    group: 'Ollama',
    description: 'Maximum number of tokens the model can process in a single request.',
  },

  {
    key: 'RAG_TOP_K',
    label: 'Top K',
    type: 'number',
    group: 'RAG',
    description: 'Number of most relevant documents passed to the model as context.',
  },
  {
    key: 'RAG_CANDIDATE_K',
    label: 'Candidate K',
    type: 'number',
    group: 'RAG',
    description: 'Number of initial candidates retrieved from the vector store before re-ranking.',
  },

  {
    key: 'EMBEDDING_BATCH_SIZE',
    label: 'Batch size',
    type: 'number',
    group: 'Embedding',
    description: 'Number of texts encoded into vectors in one batch during indexing.',
  },
];

const TUNABLE_GROUPS: TunableSpec['group'][] = ['Ollama', 'RAG', 'Embedding'];

const READ_ONLY_FIELDS: { key: keyof ReadOnlyConfig; label: string; description: string }[] = [
  {
    key: 'OLLAMA_URL',
    label: 'Ollama URL',
    description: 'Address of the language model service.',
  },
  {
    key: 'EMBEDDING_MODEL',
    label: 'Embedding model',
    description: 'Model used to convert texts into vector representations.',
  },
  {
    key: 'EMBEDDING_DEVICE',
    label: 'Device',
    description: 'Hardware used to compute embeddings (CPU or GPU).',
  },
  {
    key: 'EMBEDDING_DIM',
    label: 'Embedding dim',
    description: 'Length of the vector produced by the embedding model.',
  },
  {
    key: 'EMBEDDING_GPU_MEM_LIMIT_MB',
    label: 'GPU mem limit (MB)',
    description: 'Maximum amount of GPU memory in megabytes the embedding model may use.',
  },
];

function parseValue(spec: TunableSpec, raw: string): TunableConfig[typeof spec.key] | undefined {
  if (raw.trim() === '') return undefined;
  if (spec.type === 'number') {
    const n = Number(raw);
    return Number.isFinite(n) ? (n as TunableConfig[typeof spec.key]) : undefined;
  }
  return raw as TunableConfig[typeof spec.key];
}

export function ConfigForm() {
  const configQ = useBackendConfig();
  const { overrides, setOverride, resetAll } = useConfigOverrides();

  if (configQ.isLoading) return <CircularProgress />;
  if (configQ.error || !configQ.data) {
    return <Alert severity="error">Failed to load config: {String(configQ.error)}</Alert>;
  }

  const { tunable, read_only } = configQ.data;
  const hasOverrides = Object.keys(overrides).length > 0;

  return (
    <Box sx={{ maxWidth: 720 }}>
      {TUNABLE_GROUPS.map((group) => (
        <Box key={group} sx={{ mb: 3 }}>
          <Box sx={{ typography: 'overline', color: 'text.secondary', mb: 1 }}>{group}</Box>
          <Stack spacing={2}>
            {TUNABLE_FIELDS.filter((f) => f.group === group).map((f) => {
              const override = overrides[f.key];
              const defaultValue = tunable[f.key];
              const value = override !== undefined ? String(override) : String(defaultValue);
              const isOverridden = override !== undefined;
              return (
                <TextField
                  key={f.key}
                  label={f.label}
                  type={f.type === 'number' ? 'number' : 'text'}
                  value={value}
                  fullWidth
                  onChange={(e: ChangeEvent<HTMLInputElement>) => {
                    const parsed = parseValue(f, e.target.value);
                    if (parsed === undefined || parsed === defaultValue) {
                      setOverride(f.key, undefined);
                    } else {
                      setOverride(f.key, parsed);
                    }
                  }}
                  helperText={f.description}
                  InputProps={{
                    endAdornment: isOverridden ? (
                      <InputAdornment position="end">
                        <Chip
                          size="small"
                          label="override"
                          color="primary"
                          variant="outlined"
                          onDelete={() => setOverride(f.key, undefined)}
                        />
                      </InputAdornment>
                    ) : undefined,
                  }}
                />
              );
            })}
          </Stack>
        </Box>
      ))}

      <Box sx={{ mb: 3 }}>
        <Box sx={{ typography: 'overline', color: 'text.secondary', mb: 1 }}>Read-only</Box>
        <Stack spacing={2}>
          {READ_ONLY_FIELDS.map((f) => (
            <TextField
              key={f.key}
              label={f.label}
              value={String(read_only[f.key])}
              fullWidth
              disabled
              helperText={f.description}
            />
          ))}
        </Stack>
      </Box>

      <Stack direction="row" spacing={2}>
        <Button type="button" variant="outlined" disabled={!hasOverrides} onClick={resetAll}>
          Reset all overrides
        </Button>
      </Stack>
    </Box>
  );
}
