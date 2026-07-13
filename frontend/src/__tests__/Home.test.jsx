import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import Home from '../pages/Home';

vi.mock('../services/api', () => ({
  fetchStatistics: vi.fn(),
}));

import { fetchStatistics } from '../services/api';

describe('Home Component', () => {
  test('renders loading state initially', () => {
    fetchStatistics.mockReturnValue(new Promise(() => {}));
    render(<Home />);
    expect(screen.getByText('Palm Management System')).toBeInTheDocument();
  });

  test('renders statistics after loading', async () => {
    fetchStatistics.mockResolvedValue({
      total_palms: 100,
      total_harvest: 5000,
      average_age: 15,
      areas: [],
    });

    render(<Home />);

    await waitFor(() => {
      expect(screen.getByText('100')).toBeInTheDocument();
      expect(screen.getByText('Total Palms')).toBeInTheDocument();
    });
  });
});
