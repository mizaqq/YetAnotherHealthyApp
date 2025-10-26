import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AnalysisResultsStep } from '@/components/add-meal/AnalysisResultsStep';
import type { AnalysisResultsViewModel } from '@/types';

describe('AnalysisResultsStep', () => {
  const mockResults: AnalysisResultsViewModel = {
    totals: {
      calories: 450.5,
      protein: 25.3,
      fat: 15.7,
      carbs: 45.2,
    },
    items: [
      {
        id: 'item-1',
        analysis_run_id: 'run-1',
        ordinal: 1,
        raw_name: 'Jajka',
        matched_product_id: 'product-1',
        weight_grams: 100,
        calories: 155,
        protein: 13,
        fat: 11,
        carbs: 1.1,
        confidence: 0.95,
        created_at: '2025-01-15T12:00:00Z',
      },
      {
        id: 'item-2',
        analysis_run_id: 'run-1',
        ordinal: 2,
        raw_name: 'Chleb',
        matched_product_id: 'product-2',
        weight_grams: 50,
        calories: 130,
        protein: 4.5,
        fat: 1.2,
        carbs: 24.8,
        confidence: 0.85,
        created_at: '2025-01-15T12:00:00Z',
      },
    ],
  };

  const mockOnAccept = vi.fn();
  const mockOnRetry = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('should render MacroDisplay with results totals', () => {
      render(
        <AnalysisResultsStep
          results={mockResults}
          isLoading={false}
          onAccept={mockOnAccept}
          onRetry={mockOnRetry}
          onCancel={mockOnCancel}
        />
      );

      // MacroDisplay should show the totals
      expect(screen.getByText('Makroskładniki')).toBeInTheDocument();
      expect(screen.getByText('25.3g')).toBeInTheDocument(); // protein
      expect(screen.getByText('15.7g')).toBeInTheDocument(); // fat
      expect(screen.getByText('45.2g')).toBeInTheDocument(); // carbs
    });

    it('should render IngredientsTable with results items', () => {
      render(
        <AnalysisResultsStep
          results={mockResults}
          isLoading={false}
          onAccept={mockOnAccept}
          onRetry={mockOnRetry}
          onCancel={mockOnCancel}
        />
      );

      // IngredientsTable should show the items
      expect(screen.getByText('Jajka')).toBeInTheDocument();
      expect(screen.getByText('Chleb')).toBeInTheDocument();
    });

    it('should render section titles', () => {
      render(
        <AnalysisResultsStep
          results={mockResults}
          isLoading={false}
          onAccept={mockOnAccept}
          onRetry={mockOnRetry}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText('Podsumowanie wartości odżywczych')).toBeInTheDocument();
      expect(screen.getByText('Wykryte składniki')).toBeInTheDocument();
    });
  });

  describe('button interactions', () => {
    it('should call onAccept when accept button clicked', async () => {
      const user = userEvent.setup();
      render(
        <AnalysisResultsStep
          results={mockResults}
          isLoading={false}
          onAccept={mockOnAccept}
          onRetry={mockOnRetry}
          onCancel={mockOnCancel}
        />
      );

      const acceptButton = screen.getByRole('button', { name: /akceptuj i zapisz/i });
      await user.click(acceptButton);

      expect(mockOnAccept).toHaveBeenCalledTimes(1);
      expect(mockOnRetry).not.toHaveBeenCalled();
      expect(mockOnCancel).not.toHaveBeenCalled();
    });

    it('should call onRetry when retry button clicked', async () => {
      const user = userEvent.setup();
      render(
        <AnalysisResultsStep
          results={mockResults}
          isLoading={false}
          onAccept={mockOnAccept}
          onRetry={mockOnRetry}
          onCancel={mockOnCancel}
        />
      );

      const retryButton = screen.getByRole('button', { name: /popraw i przelicz ponownie/i });
      await user.click(retryButton);

      expect(mockOnRetry).toHaveBeenCalledTimes(1);
      expect(mockOnAccept).not.toHaveBeenCalled();
      expect(mockOnCancel).not.toHaveBeenCalled();
    });

    it('should call onCancel when cancel button clicked', async () => {
      const user = userEvent.setup();
      render(
        <AnalysisResultsStep
          results={mockResults}
          isLoading={false}
          onAccept={mockOnAccept}
          onRetry={mockOnRetry}
          onCancel={mockOnCancel}
        />
      );

      const cancelButton = screen.getByRole('button', { name: /anuluj/i });
      await user.click(cancelButton);

      expect(mockOnCancel).toHaveBeenCalledTimes(1);
      expect(mockOnAccept).not.toHaveBeenCalled();
      expect(mockOnRetry).not.toHaveBeenCalled();
    });
  });

  describe('button labels', () => {
    it('should display correct button labels', () => {
      render(
        <AnalysisResultsStep
          results={mockResults}
          isLoading={false}
          onAccept={mockOnAccept}
          onRetry={mockOnRetry}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByRole('button', { name: /anuluj/i })).toBeInTheDocument();
      expect(
        screen.getByRole('button', { name: /popraw i przelicz ponownie/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole('button', { name: /akceptuj i zapisz/i })
      ).toBeInTheDocument();
    });
  });

  describe('loading state', () => {
    it('should disable all buttons when isLoading is true', () => {
      render(
        <AnalysisResultsStep
          results={mockResults}
          isLoading={true}
          onAccept={mockOnAccept}
          onRetry={mockOnRetry}
          onCancel={mockOnCancel}
        />
      );

      const cancelButton = screen.getByRole('button', { name: /anuluj/i });
      const retryButton = screen.getByRole('button', { name: /popraw i przelicz ponownie/i });
      const acceptButton = screen.getByRole('button', { name: /akceptuj i zapisz/i });

      expect(cancelButton).toBeDisabled();
      expect(retryButton).toBeDisabled();
      expect(acceptButton).toBeDisabled();
    });

    it('should enable all buttons when isLoading is false', () => {
      render(
        <AnalysisResultsStep
          results={mockResults}
          isLoading={false}
          onAccept={mockOnAccept}
          onRetry={mockOnRetry}
          onCancel={mockOnCancel}
        />
      );

      const cancelButton = screen.getByRole('button', { name: /anuluj/i });
      const retryButton = screen.getByRole('button', { name: /popraw i przelicz ponownie/i });
      const acceptButton = screen.getByRole('button', { name: /akceptuj i zapisz/i });

      expect(cancelButton).not.toBeDisabled();
      expect(retryButton).not.toBeDisabled();
      expect(acceptButton).not.toBeDisabled();
    });
  });

  describe('edge cases', () => {
    it('should render with empty items list', () => {
      const emptyResults: AnalysisResultsViewModel = {
        totals: {
          calories: 0,
          protein: 0,
          fat: 0,
          carbs: 0,
        },
        items: [],
      };

      render(
        <AnalysisResultsStep
          results={emptyResults}
          isLoading={false}
          onAccept={mockOnAccept}
          onRetry={mockOnRetry}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText('Brak składników do wyświetlenia')).toBeInTheDocument();
    });

    it('should render with single item', () => {
      const singleItemResults: AnalysisResultsViewModel = {
        totals: {
          calories: 155,
          protein: 13,
          fat: 11,
          carbs: 1.1,
        },
        items: [mockResults.items[0]],
      };

      render(
        <AnalysisResultsStep
          results={singleItemResults}
          isLoading={false}
          onAccept={mockOnAccept}
          onRetry={mockOnRetry}
          onCancel={mockOnCancel}
        />
      );

      expect(screen.getByText('Jajka')).toBeInTheDocument();
      expect(screen.queryByText('Chleb')).not.toBeInTheDocument();
    });
  });
});

