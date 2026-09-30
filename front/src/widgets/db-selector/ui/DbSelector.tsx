import { useEffect } from 'react';
import MenuItem from '@mui/material/MenuItem';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import { useDatabases } from '../../../entities/database';

interface Props {
  value: string;
  onChange: (value: string) => void;
  allowNew?: boolean;
  label?: string;
  helperText?: string;
}

const NEW_SENTINEL = '__new__';

export function DbSelector({
  value,
  onChange,
  allowNew = false,
  label = 'Database',
  helperText,
}: Props) {
  const { data: dbs = [], isLoading } = useDatabases();
  const isNewValue = allowNew && value !== '' && !dbs.includes(value);
  const selectValue = isNewValue ? NEW_SENTINEL : value;

  useEffect(() => {
    if (!allowNew && value === '' && dbs.length > 0) onChange(dbs[0]);
  }, [allowNew, value, dbs, onChange]);

  return (
    <Stack direction="row" spacing={2} sx={{ alignItems: 'flex-start' }}>
      <TextField
        select
        label={label}
        value={selectValue}
        onChange={(e) => {
          const v = e.target.value;
          if (v === NEW_SENTINEL) onChange('');
          else onChange(v);
        }}
        helperText={helperText ?? (isLoading ? 'Loading…' : `${dbs.length} existing`)}
        sx={{ minWidth: 260 }}
      >
        {dbs.map((name) => (
          <MenuItem key={name} value={name}>
            {name}
          </MenuItem>
        ))}
        {allowNew ? (
          <MenuItem value={NEW_SENTINEL}>
            <em>+ create new…</em>
          </MenuItem>
        ) : null}
        {dbs.length === 0 && !allowNew ? (
          <MenuItem value="" disabled>
            <em>no databases yet</em>
          </MenuItem>
        ) : null}
      </TextField>
      {allowNew && (isNewValue || selectValue === NEW_SENTINEL) ? (
        <TextField
          label="New database name"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          helperText="Letters, digits, underscores"
          sx={{ minWidth: 260 }}
          autoFocus
        />
      ) : null}
    </Stack>
  );
}
