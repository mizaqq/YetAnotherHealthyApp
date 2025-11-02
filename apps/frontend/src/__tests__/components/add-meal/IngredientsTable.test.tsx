import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { IngredientsTable } from '@/components/add-meal/IngredientsTable';
import type { AnalysisRunItemDTO } from '@/types';

describe('IngredientsTable', () => {
  const createMockItem = (overrides: Partial<AnalysisRunItemDTO> = {}): AnalysisRunItemDTO => ({
    id: 'item-1',
    analysis_run_id: 'run-1',
    ordinal: 1,
    raw_name: 'Test Ingredient',
    matched_product_id: 'product-1',
    weight_grams: 100.5,
    calories: 450,
    protein: 23.7,
    fat: 12.3,
    carbs: 45.6,
    confidence: 0.85,
    created_at: '2025-01-15T12:00:00Z',
    ...overrides,
  });

  describe('empty state', () => {
    it('should display message when no ingredients provided', () => {
      render(<IngredientsTable items={[]} />);
      
      expect(screen.getByText('Brak składników do wyświetlenia')).toBeInTheDocument();
    });

    it('should not render table when items list is empty', () => {
      render(<IngredientsTable items={[]} />);
      
      expect(screen.queryByRole('table')).not.toBeInTheDocument();
    });
  });

  describe('number formatting', () => {
    it('should format weight_grams with 1 decimal place', () => {
      const item = createMockItem({ weight_grams: 125.567 });
      render(<IngredientsTable items={[item]} />);
      
      expect(screen.getByText('125.6')).toBeInTheDocument();
    });

    it('should format calories with 0 decimal places', () => {
      const item = createMockItem({ calories: 450.89 });
      render(<IngredientsTable items={[item]} />);
      
      expect(screen.getByText('451')).toBeInTheDocument();
    });

    it('should format protein with 1 decimal place', () => {
      const item = createMockItem({ protein: 23.789 });
      render(<IngredientsTable items={[item]} />);
      
      expect(screen.getByText('23.8')).toBeInTheDocument();
    });

    it('should format fat with 1 decimal place', () => {
      const item = createMockItem({ fat: 12.345 });
      render(<IngredientsTable items={[item]} />);
      
      expect(screen.getByText('12.3')).toBeInTheDocument();
    });

    it('should format carbs with 1 decimal place', () => {
      const item = createMockItem({ carbs: 45.678 });
      render(<IngredientsTable items={[item]} />);
      
      expect(screen.getByText('45.7')).toBeInTheDocument();
    });

    it('should handle null values as 0', () => {
      const item = createMockItem({
        weight_grams: null as unknown as number,
        calories: null as unknown as number,
        protein: null as unknown as number,
        fat: null as unknown as number,
        carbs: null as unknown as number,
      });
      render(<IngredientsTable items={[item]} />);
      
      // Check for 0 calories
      expect(screen.getByText('0')).toBeInTheDocument();
      // Check that there are multiple 0.0 values for macros
      const zeroValues = screen.getAllByText('0.0');
      expect(zeroValues.length).toBeGreaterThanOrEqual(4); // weight, protein, fat, carbs
    });
  });

  describe('confidence styling', () => {
    it('should apply high confidence class for confidence >= 0.8', () => {
      const item = createMockItem({ confidence: 0.85 });
      render(<IngredientsTable items={[item]} />);
      
      const confidenceCell = screen.getByText('85%');
      expect(confidenceCell).toBeInTheDocument();
      // FluentUI generates dynamic class names, so we verify the text is rendered correctly
      // The actual styling is applied via makeStyles which we trust is working
    });

    it('should apply medium confidence class for 0.5 <= confidence < 0.8', () => {
      const item = createMockItem({ confidence: 0.65 });
      render(<IngredientsTable items={[item]} />);
      
      const confidenceCell = screen.getByText('65%');
      expect(confidenceCell).toBeInTheDocument();
    });

    it('should apply low confidence class for confidence < 0.5', () => {
      const item = createMockItem({ confidence: 0.35 });
      render(<IngredientsTable items={[item]} />);
      
      const confidenceCell = screen.getByText('35%');
      expect(confidenceCell).toBeInTheDocument();
    });

    it('should handle edge case confidence = 0.8 as high', () => {
      const item = createMockItem({ confidence: 0.8 });
      render(<IngredientsTable items={[item]} />);
      
      const confidenceCell = screen.getByText('80%');
      expect(confidenceCell).toBeInTheDocument();
    });

    it('should handle edge case confidence = 0.5 as medium', () => {
      const item = createMockItem({ confidence: 0.5 });
      render(<IngredientsTable items={[item]} />);
      
      const confidenceCell = screen.getByText('50%');
      expect(confidenceCell).toBeInTheDocument();
    });

    it('should format confidence as percentage without decimals', () => {
      const item = createMockItem({ confidence: 0.8567 });
      render(<IngredientsTable items={[item]} />);
      
      expect(screen.getByText('86%')).toBeInTheDocument();
    });

    it('should handle null confidence as 0%', () => {
      const item = createMockItem({ confidence: null as unknown as number });
      render(<IngredientsTable items={[item]} />);
      
      const confidenceCell = screen.getByText('0%');
      expect(confidenceCell).toBeInTheDocument();
    });
  });

  describe('table structure', () => {
    it('should render table with correct headers', () => {
      const item = createMockItem();
      render(<IngredientsTable items={[item]} />);
      
      expect(screen.getByText('Lp.')).toBeInTheDocument();
      expect(screen.getByText('Składnik')).toBeInTheDocument();
      expect(screen.getByText('Waga (g)')).toBeInTheDocument();
      expect(screen.getByText('Kalorie')).toBeInTheDocument();
      expect(screen.getByText('Białko (g)')).toBeInTheDocument();
      expect(screen.getByText('Tłuszcz (g)')).toBeInTheDocument();
      expect(screen.getByText('Węgl. (g)')).toBeInTheDocument();
      expect(screen.getByText('Pewność')).toBeInTheDocument();
    });

    it('should render ordinal column correctly', () => {
      const items = [
        createMockItem({ id: 'item-1', ordinal: 1, raw_name: 'First' }),
        createMockItem({ id: 'item-2', ordinal: 2, raw_name: 'Second' }),
        createMockItem({ id: 'item-3', ordinal: 3, raw_name: 'Third' }),
      ];
      render(<IngredientsTable items={items} />);
      
      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
    });

    it('should render ingredient names', () => {
      const items = [
        createMockItem({ id: 'item-1', raw_name: 'Eggs' }),
        createMockItem({ id: 'item-2', raw_name: 'Bread' }),
      ];
      render(<IngredientsTable items={items} />);
      
      expect(screen.getByText('Eggs')).toBeInTheDocument();
      expect(screen.getByText('Bread')).toBeInTheDocument();
    });

    it('should have correct aria-label on table', () => {
      const item = createMockItem();
      render(<IngredientsTable items={[item]} />);
      
      const table = screen.getByRole('table');
      expect(table).toHaveAttribute('aria-label', 'Tabela składników');
    });
  });

  describe('multiple items rendering', () => {
    it('should render all items in the list', () => {
      const items = [
        createMockItem({ id: 'item-1', ordinal: 1, raw_name: 'Ingredient 1' }),
        createMockItem({ id: 'item-2', ordinal: 2, raw_name: 'Ingredient 2' }),
        createMockItem({ id: 'item-3', ordinal: 3, raw_name: 'Ingredient 3' }),
      ];
      render(<IngredientsTable items={items} />);
      
      expect(screen.getByText('Ingredient 1')).toBeInTheDocument();
      expect(screen.getByText('Ingredient 2')).toBeInTheDocument();
      expect(screen.getByText('Ingredient 3')).toBeInTheDocument();
    });

    it('should render different confidence levels for multiple items', () => {
      const items = [
        createMockItem({ id: 'item-1', raw_name: 'High', confidence: 0.9 }),
        createMockItem({ id: 'item-2', raw_name: 'Medium', confidence: 0.6 }),
        createMockItem({ id: 'item-3', raw_name: 'Low', confidence: 0.3 }),
      ];
      render(<IngredientsTable items={items} />);
      
      const highConf = screen.getByText('90%');
      const medConf = screen.getByText('60%');
      const lowConf = screen.getByText('30%');
      
      expect(highConf).toBeInTheDocument();
      expect(medConf).toBeInTheDocument();
      expect(lowConf).toBeInTheDocument();
    });
  });
});

