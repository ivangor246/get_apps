import { useEffect, useMemo, useState, type ChangeEvent, type FormEvent } from 'react';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import InputAdornment from '@mui/material/InputAdornment';
import MenuItem from '@mui/material/MenuItem';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import { useConfig, useConfigDefaults, useUpdateConfig, type AppConfig } from '../../../entities/config';

type FieldSpec = {
  key: keyof AppConfig;
  label: string;
  type: 'text' | 'number' | 'select';
  options?: string[];
  group: 'Ollama' | 'Embedding' | 'RAG' | 'API';
};

const FIELDS: FieldSpec[] = [
  { key: 'OLLAMA_URL', label: 'Ollama URL', type: 'text', group: 'Ollama' },
  { key: 'OLLAMA_LLM_MODEL', label: 'LLM model', type: 'text', group: 'Ollama' },
  { key: 'OLLAMA_TIMEOUT', label: 'Timeout (s)', type: 'number', group: 'Ollama' },

  { key: 'EMBEDDING_MODEL', label: 'Embedding model', type: 'text', group: 'Embedding' },
  { key: 'EMBEDDING_DEVICE', label: 'Device', type: 'select', options: ['cuda', 'cpu'], group: 'Embedding' },
  { key: 'EMBEDDING_DIM', label: 'Dim', type: 'number', group: 'Embedding' },
  { key: 'EMBEDDING_BATCH_SIZE', label: 'Batch size', type: 'number', group: 'Embedding' },
  { key: 'EMBEDDING_GPU_MEM_LIMIT_MB', label: 'GPU mem limit (MB)', type: 'number', group: 'Embedding' },

  { key: 'RAG_TOP_K', label: 'Top K', type: 'number', group: 'RAG' },
  { key: 'RAG_CANDIDATE_K', label: 'Candidate K', type: 'number', group: 'RAG' },

  { key: 'API_HOST', label: 'API host', type: 'text', group: 'API' },
  { key: 'API_PORT', label: 'API port', type: 'number', group: 'API' },
];

const GROUPS: FieldSpec['group'][] = ['Ollama', 'Embedding', 'RAG', 'API'];

function toFormValues(config: AppConfig): Record<string, string> {
  return Object.fromEntries(Object.entries(config).map(([k, v]) => [k, String(v)]));
}

function parseValues(values: Record<string, string>): AppConfig {
  const out: Record<string, unknown> = {};
  for (const f of FIELDS) {
    const raw = values[f.key as string];
    out[f.key] = f.type === 'number' ? Number(raw) : raw;
  }
  return out as AppConfig;
}

export function ConfigForm() {
  const configQ = useConfig();
  const defaultsQ = useConfigDefaults();
  const update = useUpdateConfig();

  const [values, setValues] = useState<Record<string, string>>({});

  useEffect(() => {
    if (configQ.data) setValues(toFormValues(configQ.data));
  }, [configQ.data]);

  const defaults = defaultsQ.data;
  const dirty = useMemo(() => {
    if (!configQ.data) return false;
    const current = toFormValues(configQ.data);
    return FIELDS.some((f) => values[f.key as string] !== current[f.key as string]);
  }, [values, configQ.data]);

  if (configQ.isLoading || defaultsQ.isLoading) {
    return <CircularProgress />;
  }
  if (configQ.error) {
    return <Alert severity="error">Failed to load config: {String(configQ.error)}</Alert>;
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    update.mutate(parseValues(values));
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ maxWidth: 720 }}>
      {GROUPS.map((group) => (
        <Box key={group} sx={{ mb: 3 }}>
          <Box sx={{ typography: 'overline', color: 'text.secondary', mb: 1 }}>{group}</Box>
          <Stack spacing={2}>
            {FIELDS.filter((f) => f.group === group).map((f) => {
              const value = values[f.key as string] ?? '';
              const defaultValue = defaults ? String(defaults[f.key]) : '';
              const isOverridden = defaults ? value !== defaultValue : false;
              const common = {
                key: f.key as string,
                label: f.label,
                value,
                fullWidth: true,
                onChange: (e: ChangeEvent<HTMLInputElement>) =>
                  setValues((prev) => ({ ...prev, [f.key]: e.target.value })),
                helperText: `Default: ${defaultValue}`,
                InputProps: {
                  endAdornment: isOverridden ? (
                    <InputAdornment position="end">
                      <Chip size="small" label="override" color="primary" variant="outlined" />
                    </InputAdornment>
                  ) : undefined,
                },
              };
              if (f.type === 'select') {
                return (
                  <TextField {...common} select>
                    {(f.options ?? []).map((opt) => (
                      <MenuItem key={opt} value={opt}>
                        {opt}
                      </MenuItem>
                    ))}
                  </TextField>
                );
              }
              return <TextField {...common} type={f.type === 'number' ? 'number' : 'text'} />;
            })}
          </Stack>
        </Box>
      ))}

      {update.error ? <Alert severity="error" sx={{ mb: 2 }}>{String(update.error)}</Alert> : null}
      {update.isSuccess && !dirty ? <Alert severity="success" sx={{ mb: 2 }}>Saved.</Alert> : null}

      <Stack direction="row" spacing={2}>
        <Button
          type="submit"
          variant="contained"
          disabled={!dirty || update.isPending}
        >
          {update.isPending ? 'Saving…' : 'Save'}
        </Button>
        <Button
          type="button"
          variant="outlined"
          disabled={!dirty || update.isPending}
          onClick={() => configQ.data && setValues(toFormValues(configQ.data))}
        >
          Reset
        </Button>
        <Button
          type="button"
          color="inherit"
          disabled={!defaults || update.isPending}
          onClick={() => defaults && setValues(toFormValues(defaults))}
        >
          Load defaults
        </Button>
      </Stack>
    </Box>
  );
}
