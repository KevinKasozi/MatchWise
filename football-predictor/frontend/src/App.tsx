import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from './components/Layout';
import Home from './pages/Home';
import Clubs from './pages/Clubs';
import Competitions from './pages/Competitions';
import Fixtures from './pages/Fixtures';
import Predictions from './pages/Predictions';

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/clubs" element={<Clubs />} />
            <Route path="/competitions" element={<Competitions />} />
            <Route path="/fixtures" element={<Fixtures />} />
            <Route path="/predictions" element={<Predictions />} />
          </Routes>
        </Layout>
      </Router>
    </QueryClientProvider>
  );
}
