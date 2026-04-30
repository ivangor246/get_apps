import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Tooltip from '@mui/material/Tooltip';
import { useSystemStatus, type OllamaStatus } from '../../../entities/system-status';

type ChipColor = 'default' | 'success' | 'warning' | 'error';

const OLLAMA_LABELS: Record<OllamaStatus, string> = {
  pending: 'Ollama: pending',
  starting_server: 'Ollama: starting server…',
  checking_model: 'Ollama: checking model…',
  model_missing: 'Ollama: model missing',
  warming_up: 'Ollama: warming up…',
  ready: 'Ollama: ready',
  error: 'Ollama: error',
};

const OLLAMA_COLORS: Record<OllamaStatus, ChipColor> = {
  pending: 'warning',
  starting_server: 'warning',
  checking_model: 'warning',
  model_missing: 'error',
  warming_up: 'warning',
  ready: 'success',
  error: 'error',
};

export function StatusIndicator() {
  const { data, isError, isLoading } = useSystemStatus();

  if (isError) {
    return (
      <Box sx={{ display: 'flex', gap: 1, mr: 1 }}>
        <Tooltip title="Backend is not reachable. Is the API server running?">
          <Chip size="small" color="error" label="Backend: offline" />
        </Tooltip>
      </Box>
    );
  }

  if (isLoading || !data) {
    return (
      <Box sx={{ display: 'flex', gap: 1, mr: 1 }}>
        <Chip size="small" color="default" label="Backend: …" />
      </Box>
    );
  }

  const ollama = data.ollama;
  const tooltip = ollama.detail
    ? `${ollama.detail}${ollama.model ? `\nmodel: ${ollama.model}` : ''}`
    : ollama.model
      ? `model: ${ollama.model}`
      : '';

  return (
    <Box sx={{ display: 'flex', gap: 1, mr: 1 }}>
      <Chip size="small" color="success" label="Backend: ready" />
      <Tooltip title={tooltip} placement="bottom-end">
        <Chip
          size="small"
          color={OLLAMA_COLORS[ollama.status]}
          label={OLLAMA_LABELS[ollama.status]}
        />
      </Tooltip>
    </Box>
  );
}
