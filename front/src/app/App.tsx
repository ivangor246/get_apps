import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import { Navigate, Route, Routes } from 'react-router-dom';
import { AppHeader } from '../widgets/app-header';
import { HomePage } from '../pages/home';
import { CollectionPage } from '../pages/collection';
import { IndexingPage } from '../pages/indexing';
import { SettingsPage } from '../pages/settings';
import { withProviders } from './providers';

function Layout() {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppHeader />
      <Container maxWidth="lg" sx={{ py: 4, flexGrow: 1 }}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/collection" element={<CollectionPage />} />
          <Route path="/indexing" element={<IndexingPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Container>
    </Box>
  );
}

export default function App() {
  return withProviders(<Layout />);
}
