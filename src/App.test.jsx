import { render, screen } from '@testing-library/react';
import App from './App';

test('renders MatchWise welcome message', () => {
  render(<App />);
  expect(screen.getByText(/MatchWise/i)).toBeInTheDocument();
  expect(screen.getByText(/football data platform/i)).toBeInTheDocument();
}); 