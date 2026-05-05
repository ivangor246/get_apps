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
};

const TUNABLE_FIELDS: TunableSpec[] = [
  { key: 'OLLAMA_LLM_MODEL', label: 'LLM model', type: 'text', group: 'Ollama' },
  { key: 'OLLAMA_TIMEOUT', label: 'Timeout (s)', type: 'number', group: 'Ollama' },
  { key: 'OLLAMA_CONTEXT_SIZE', label: 'Context size', type: 'number', group: 'Ollama' },

  { key: 'RAG_TOP_K', label: 'Top K', type: 'number', group: 'RAG' },
  { key: 'RAG_CANDIDATE_K', label: 'Candidate K', type: 'number', group: 'RAG' },

  { key: 'EMBEDDING_BATCH_SIZE', label: 'Batch size', type: 'number', group: 'Embedding' },
];

const TUNABLE_GROUPS: TunableSpec['group'][] = ['Ollama', 'RAG', 'Embedding'];

const READ_ONLY_FIELDS: { key: keyof ReadOnlyConfig; label: string }[] = [
  { key: 'OLLAMA_URL', label: 'Ollama URL' },
  { key: 'EMBEDDING_MODEL', label: 'Embedding model' },
  { key: 'EMBEDDING_DEVICE', label: 'Device' },
  { key: 'EMBEDDING_DIM', label: 'Embedding dim' },
  { key: 'EMBEDDING_GPU_MEM_LIMIT_MB', label: 'GPU mem limit (MB)' },
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
                  helperText={`Default: ${defaultValue}`}
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
        <Box sx={{ typography: 'overline', color: 'text.secondary', mb: 1 }}>Read-only (backend startup)</Box>
        <Stack spacing={2}>
          {READ_ONLY_FIELDS.map((f) => (
            <TextField
              key={f.key}
              label={f.label}
              value={String(read_only[f.key])}
              fullWidth
              disabled
              helperText="Set in back/src/app/core/config.py; restart required"
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
