import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import Link from '@mui/material/Link';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import { SubmitRagQueryForm } from '../../../features/submit-rag-query';
import {
  useRagQuery,
  type AppliedFilters as Filters,
  type SourceApp,
} from '../../../entities/rag-result';

function FiltersChips({ filters }: { filters: Filters }) {
  const chips: string[] = [];
  if (filters.min_downloads != null) chips.push(`downloads ≥ ${filters.min_downloads.toLocaleString()}`);
  if (filters.max_downloads != null) chips.push(`downloads ≤ ${filters.max_downloads.toLocaleString()}`);
  if (filters.min_rating != null) chips.push(`rating ≥ ${filters.min_rating}`);
  if (filters.above_median_downloads) chips.push('above median downloads');
  for (const c of filters.categories_any) chips.push(`category: ${c}`);
  if (chips.length === 0) return null;
  return (
    <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1, mb: 2 }}>
      {chips.map((c) => (
        <Chip key={c} label={c} size="small" variant="outlined" />
      ))}
    </Stack>
  );
}

function SourceCard({ src }: { src: SourceApp }) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Stack direction="row" spacing={2} sx={{ alignItems: 'baseline', mb: 1 }}>
          <Link href={src.url} target="_blank" rel="noopener" sx={{ fontWeight: 600 }}>
            {src.name ?? src.app_id}
          </Link>
          <Typography variant="caption" color="text.secondary">
            {src.app_id}
          </Typography>
          <Box sx={{ flexGrow: 1 }} />
          <Typography variant="caption" color="text.secondary">
            dist {src.distance.toFixed(3)}
          </Typography>
        </Stack>
        <Stack direction="row" spacing={2} sx={{ flexWrap: 'wrap', gap: 1 }}>
          {src.rating != null ? <Chip size="small" label={`★ ${src.rating}`} /> : null}
          {src.downloads != null ? (
            <Chip size="small" label={`${src.downloads.toLocaleString()} downloads`} />
          ) : null}
          {src.categories.map((c) => (
            <Chip key={c} size="small" label={c} variant="outlined" />
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
}

export function HomePage() {
  const rag = useRagQuery();

  return (
    <>
      <Typography variant="h4" gutterBottom>
        Query
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Ask a natural-language question over an indexed database.
      </Typography>

      <SubmitRagQueryForm loading={rag.isPending} onSubmit={(payload) => rag.mutate(payload)} />

      {rag.error ? (
        <Alert severity="error" sx={{ mt: 3 }}>
          {String(rag.error)}
        </Alert>
      ) : null}

      {rag.data ? (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" gutterBottom>
            Answer
          </Typography>
          <Typography sx={{ whiteSpace: 'pre-wrap', mb: 3 }}>{rag.data.answer}</Typography>

          <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1, mb: 1 }}>
            <Chip label={`intent: ${rag.data.intent}`} size="small" variant="outlined" />
            {rag.data.language ? (
              <Chip label={`lang: ${rag.data.language}`} size="small" variant="outlined" />
            ) : null}
            <Chip label={`iterations: ${rag.data.iterations}`} size="small" variant="outlined" />
          </Stack>
          <FiltersChips filters={rag.data.filters} />

          <Divider sx={{ my: 2 }} />

          <Typography variant="h6" gutterBottom>
            Sources ({rag.data.sources.length})
          </Typography>
          <Stack spacing={2}>
            {rag.data.sources.map((s) => (
              <SourceCard key={s.app_id} src={s} />
            ))}
          </Stack>
        </Box>
      ) : null}
    </>
  );
}
