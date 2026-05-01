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
import { useQueryClient } from '@tanstack/react-query';
import { useUpdateConfig } from '../../../entities/config';
import {
  OLLAMA_MODELS_KEY,
  useLoadOllamaModel,
  useOllamaModels,
} from '../../../entities/ollama';

export function ModelPicker() {
  const qc = useQueryClient();
  const modelsQ = useOllamaModels();
  const updateConfig = useUpdateConfig();
  const loadMutation = useLoadOllamaModel();

  const data = modelsQ.data;
  const current = data?.current ?? '';
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

  const handleSelect = (value: string) => {
    if (value === current) return;
    updateConfig.mutate(
      { OLLAMA_LLM_MODEL: value },
      { onSuccess: () => qc.invalidateQueries({ queryKey: OLLAMA_MODELS_KEY }) },
    );
  };

  return (
    <Box sx={{ mb: 4 }}>
      <Box sx={{ typography: 'overline', color: 'text.secondary', mb: 1 }}>AI Model</Box>

      {modelsQ.isLoading ? (
        <CircularProgress size={24} />
      ) : modelsQ.error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load models: {String(modelsQ.error)}
        </Alert>
      ) : (
        <>
          <Stack direction="row" spacing={1} sx={{ alignItems: 'flex-start', mb: 1 }}>
            <TextField
              select
              label="Active model"
              value={current}
              onChange={(e) => handleSelect(e.target.value)}
              disabled={updateConfig.isPending || models.length === 0}
              sx={{ minWidth: 320 }}
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

          <Typography variant="caption" color="text.secondary">
            Status: {status} · {downloadedCount} local model{downloadedCount === 1 ? '' : 's'}
          </Typography>

          {updateConfig.error ? (
            <Alert severity="error" sx={{ mt: 2 }}>
              Failed to save model selection: {String(updateConfig.error)}
            </Alert>
          ) : null}
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
