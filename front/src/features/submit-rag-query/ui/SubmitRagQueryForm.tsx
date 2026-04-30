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

  const handle = (e: FormEvent) => {
    e.preventDefault();
    onSubmit({
      db_name: dbName.trim(),
      query: query.trim(),
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

      <Button
        type="submit"
        variant="contained"
        disabled={loading || dbName.trim() === '' || query.trim() === ''}
        sx={{ alignSelf: 'flex-start' }}
      >
        {loading ? 'Running…' : 'Ask'}
      </Button>
    </Stack>
  );
}
