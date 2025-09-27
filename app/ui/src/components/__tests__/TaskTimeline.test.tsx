import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import TaskTimeline from '@/components/TaskTimeline';
import { get } from '@/lib/api';

// Mock the api utility
jest.mock('@/lib/api', () => ({
  get: jest.fn(),
}));

const mockGet = get as jest.Mock;

const mockEvents = [
  {
    timestamp: '2025-08-30T10:00:00Z',
    kind: 'context',
    icon: '📝',
    title: 'Context collected',
    description: 'Size: 4.5kB; model: gemini-2.5-flash; tokens: 1250',
    severity: 'info' as const,
    links: { log_id: 'corr-123' },
    details: { prompt_tokens: 1200, completion_tokens: 50, model: 'gemini-2.5-flash' },
  },
  {
    timestamp: '2025-08-30T10:05:00Z',
    kind: 'generation',
    icon: '⚡',
    title: 'Code generated',
    description: 'Created 2 files, changed 1',
    severity: 'info' as const,
    links: { artifact: '/artifacts/abc.zip' },
    details: { files_created: ['a.py', 'b.py'], files_changed: ['c.py'] },
  },
];

describe('TaskTimeline', () => {
  beforeEach(() => {
    mockGet.mockClear();
  });

  it('should render loading state initially', () => {
    mockGet.mockImplementation(() => new Promise(() => {})); // Never resolves
    render(<TaskTimeline taskId="123" />);
    // Loading state shows skeleton animation, not text
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('should render error state', async () => {
    mockGet.mockRejectedValue(new Error('API Error'));
    render(<TaskTimeline taskId="123" />);
    expect(await screen.findByText('Ошибка загрузки трассировки')).toBeInTheDocument();
  });

  it('should render empty state', async () => {
    mockGet.mockResolvedValue({ data: { items: [], total: 0 } });
    render(<TaskTimeline taskId="123" />);
    expect(await screen.findByText('Событий пока нет')).toBeInTheDocument();
  });

  it('should render events and toggle details visibility', async () => {
    mockGet.mockResolvedValue({ data: { items: mockEvents, total: mockEvents.length } });
    render(<TaskTimeline taskId="123" />);

    // Wait for events to be rendered
    expect(await screen.findByText('Context collected')).toBeInTheDocument();
    expect(screen.getByText('Code generated')).toBeInTheDocument();

    // Details should be hidden initially
    expect(screen.queryByText('prompt_tokens')).not.toBeInTheDocument();

    // Find and click the 'Show Details' button for the first event
    const showDetailsButton = screen.getAllByText('Показать детали')[0];
    fireEvent.click(showDetailsButton);

    // Wait for details to appear and check content
    await waitFor(() => {
      expect(screen.getByText(/prompt_tokens/i)).toBeInTheDocument();
      expect(screen.getAllByText(/gemini-2.5-flash/i)).toHaveLength(2); // One in description, one in details
    });

    // Check that button text changed
    expect(screen.getByText('Скрыть детали')).toBeInTheDocument();

    // Click the 'Hide Details' button (now it shows "Скрыть детали")
    fireEvent.click(screen.getByText('Скрыть детали'));

    // Wait for details to disappear
    await waitFor(() => {
      expect(screen.queryByText(/prompt_tokens/i)).not.toBeInTheDocument();
    });
  });
});