import { useState, type FormEvent } from 'react';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import { DbSelector } from '../../../widgets/db-selector';
import type { RAGQueryPayload } from '../../../entities/rag-result';

interface Props {
  loading?: boolean;
  onSubmit: (payload: RAGQueryPayload) => void;
}

export function SubmitRagQueryForm({ loading, onSubmit }: Props) {
  const [dbName, setDbName] = useState('');
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(20);

  const handle = (e: FormEvent) => {
    e.preventDefault();
    onSubmit({
      db_name: dbName.trim(),
      query: query.trim(),
      top_k: topK,
    });
  };

  return (
    <Stack component="form" onSubmit={handle} spacing={2}>
      <DbSelector value={dbName} onChange={setDbName} />

      <TextField
        label="Query"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        multiline
        minRows={3}
        placeholder="E.g. Find popular photo editors with rating above 4.5"
      />

      <Stack direction="row" spacing={2} sx={{ alignItems: 'center' }}>
        <TextField
          type="number"
          label="Top K"
          value={topK}
          onChange={(e) => setTopK(Math.max(1, Math.min(100, Number(e.target.value) || 1)))}
          sx={{ width: 140 }}
        />
        <Button
          type="submit"
          variant="contained"
          disabled={loading || dbName.trim() === '' || query.trim() === ''}
        >
          {loading ? 'Running…' : 'Ask'}
        </Button>
      </Stack>
    </Stack>
  );
}
