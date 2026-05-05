import { useEffect, useState } from 'react';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import IconButton from '@mui/material/IconButton';
import MenuItem from '@mui/material/MenuItem';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import RefreshIcon from '@mui/icons-material/Refresh';
import { useBackendConfig } from '../../../entities/config';
import { useLoadOllamaModel, useOllamaModels } from '../../../entities/ollama';
import { useConfigOverrides } from '../../../shared/config';

export function ModelPicker() {
  const modelsQ = useOllamaModels();
  const configQ = useBackendConfig();
  const { overrides, setOverride } = useConfigOverrides();
  const loadMutation = useLoadOllamaModel();

  const data = modelsQ.data;
  const backendDefault = data?.current ?? configQ.data?.tunable.OLLAMA_LLM_MODEL ?? '';
  const current = overrides.OLLAMA_LLM_MODEL ?? backendDefault;
  const models = data?.models ?? [];
  const currentInfo = models.find((m) => m.name === current);
  const downloadedCount = models.filter((m) => m.downloaded).length;
  const status = !currentInfo
    ? 'unknown'
    : !currentInfo.downloaded
      ? 'not downloaded'
      : currentInfo.loaded
        ? 'loaded'
        : 'not loaded';

  const defaultCtx = configQ.data?.tunable.OLLAMA_CONTEXT_SIZE ?? 0;
  const effectiveCtx = overrides.OLLAMA_CONTEXT_SIZE ?? defaultCtx;
  const [ctxInput, setCtxInput] = useState<string>('');
  useEffect(() => {
    if (effectiveCtx > 0) setCtxInput(String(effectiveCtx));
  }, [effectiveCtx]);

  const defaultTimeout = configQ.data?.tunable.OLLAMA_TIMEOUT ?? 0;
  const effectiveTimeout = overrides.OLLAMA_TIMEOUT ?? defaultTimeout;
  const [timeoutInput, setTimeoutInput] = useState<string>('');
  useEffect(() => {
    if (effectiveTimeout > 0) setTimeoutInput(String(effectiveTimeout));
  }, [effectiveTimeout]);

  const handleSelect = (value: string) => {
    if (value === current) return;
    if (value === backendDefault) {
      setOverride('OLLAMA_LLM_MODEL', undefined);
    } else {
      setOverride('OLLAMA_LLM_MODEL', value);
    }
  };

  const commitContext = () => {
    const parsed = Number(ctxInput);
    if (!Number.isFinite(parsed) || parsed <= 0) {
      setCtxInput(String(effectiveCtx));
      return;
    }
    const rounded = Math.floor(parsed);
    if (rounded === defaultCtx) {
      setOverride('OLLAMA_CONTEXT_SIZE', undefined);
    } else {
      setOverride('OLLAMA_CONTEXT_SIZE', rounded);
    }
  };

  const commitTimeout = () => {
    const parsed = Number(timeoutInput);
    if (!Number.isFinite(parsed) || parsed <= 0) {
      setTimeoutInput(String(effectiveTimeout));
      return;
    }
    const rounded = Math.floor(parsed);
    if (rounded === defaultTimeout) {
      setOverride('OLLAMA_TIMEOUT', undefined);
    } else {
      setOverride('OLLAMA_TIMEOUT', rounded);
    }
  };

  const isModelOverridden = overrides.OLLAMA_LLM_MODEL !== undefined;

  return (
    <Box sx={{ mb: 4, maxWidth: 720 }}>
      <Box sx={{ typography: 'overline', color: 'text.secondary', mb: 1 }}>AI Model</Box>

      {modelsQ.isLoading ? (
        <CircularProgress size={24} />
      ) : modelsQ.error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load models: {String(modelsQ.error)}
        </Alert>
      ) : (
        <>
          <Stack direction="row" spacing={1} sx={{ alignItems: 'flex-start' }}>
            <TextField
              select
              label="Active model"
              value={current}
              onChange={(e) => handleSelect(e.target.value)}
              disabled={models.length === 0}
              sx={{ minWidth: 320 }}
              helperText={isModelOverridden ? `Override (default: ${backendDefault})` : undefined}
            >
              {models.length === 0 ? (
                <MenuItem value="" disabled>
                  <em>no local models</em>
                </MenuItem>
              ) : null}
              {models.map((m) => (
                <MenuItem key={m.name} value={m.name}>
                  <Stack direction="row" spacing={1} sx={{ alignItems: 'center', width: '100%' }}>
                    <span>{m.name}</span>
                    <Box sx={{ flexGrow: 1 }} />
                    {m.loaded ? <Chip size="small" label="loaded" color="success" /> : null}
                    {!m.downloaded ? (
                      <Chip size="small" label="not downloaded" variant="outlined" />
                    ) : null}
                  </Stack>
                </MenuItem>
              ))}
            </TextField>
            <IconButton
              aria-label="refresh"
              onClick={() => modelsQ.refetch()}
              disabled={modelsQ.isFetching}
            >
              <RefreshIcon />
            </IconButton>
            <Button
              variant="contained"
              onClick={() => current && loadMutation.mutate(current)}
              disabled={
                !current
                || !currentInfo?.downloaded
                || currentInfo.loaded
                || loadMutation.isPending
              }
            >
              {loadMutation.isPending ? 'Starting…' : 'Start'}
            </Button>
          </Stack>

          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ display: 'block', mt: 0.5, mb: 3 }}
          >
            Status: {status} · {downloadedCount} local model{downloadedCount === 1 ? '' : 's'}
          </Typography>

          <Stack spacing={2} sx={{ mb: 1 }}>
            <TextField
              label="Context size (tokens)"
              type="number"
              value={ctxInput}
              onChange={(e) => setCtxInput(e.target.value)}
              onBlur={commitContext}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  (e.target as HTMLInputElement).blur();
                }
              }}
              disabled={configQ.isLoading}
              fullWidth
              inputProps={{ min: 1, step: 256 }}
              helperText="Maximum number of tokens the model can process in a single request."
            />
            <TextField
              label="Timeout (s)"
              type="number"
              value={timeoutInput}
              onChange={(e) => setTimeoutInput(e.target.value)}
              onBlur={commitTimeout}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  (e.target as HTMLInputElement).blur();
                }
              }}
              disabled={configQ.isLoading}
              fullWidth
              inputProps={{ min: 1, step: 1 }}
              helperText="Maximum time in seconds to wait for a model response."
            />
          </Stack>

          {loadMutation.error ? (
            <Alert severity="error" sx={{ mt: 2 }}>
              Failed to start model: {String(loadMutation.error)}
            </Alert>
          ) : null}
        </>
      )}
    </Box>
  );
}
