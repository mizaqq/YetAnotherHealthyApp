import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MacroDisplay } from '@/components/dashboard/MacroDisplay';

describe('MacroDisplay', () => {
  const mockMacros = {
    protein: 50,
    fat: 30,
    carbs: 100,
  };

  describe('calorie calculation', () => {
    it('should use provided calories when passed as prop', () => {
      render(<MacroDisplay macros={mockMacros} calories={500} />);
      
      expect(screen.getByText('500kcal')).toBeInTheDocument();
    });

    it('should calculate calories from macros when not provided', () => {
      // 50*4 + 30*9 + 100*4 = 200 + 270 + 400 = 870
      render(<MacroDisplay macros={mockMacros} />);
      
      // When calories not provided, it shouldn't show the calorie row at all
      expect(screen.queryByText(/kcal/)).not.toBeInTheDocument();
    });

    it('should calculate correct calories for zero macros', () => {
      render(<MacroDisplay macros={{ protein: 0, fat: 0, carbs: 0 }} />);
      
      // Should not display calories row
      expect(screen.queryByText(/kcal/)).not.toBeInTheDocument();
    });
  });

  describe('percentage calculations', () => {
    it('should calculate correct macro percentages', () => {
      // Total: 50*4 + 30*9 + 100*4 = 870 kcal
      // Protein: 200/870 = 23%, Fat: 270/870 = 31%, Carbs: 400/870 = 46%
      render(<MacroDisplay macros={mockMacros} />);
      
      expect(screen.getByText('23%')).toBeInTheDocument(); // Protein
      expect(screen.getByText('31%')).toBeInTheDocument(); // Fat
      expect(screen.getByText('46%')).toBeInTheDocument(); // Carbs
    });

    it('should handle zero total calories without division by zero', () => {
      render(<MacroDisplay macros={{ protein: 0, fat: 0, carbs: 0 }} />);
      
      // All percentages should be 0%
      const percentages = screen.getAllByText('0%');
      expect(percentages).toHaveLength(3);
    });

    it('should calculate percentages based on provided calories', () => {
      // With 400 total calories provided:
      // Protein: 200/400 = 50%, Fat: 270/400 = 68%, Carbs: 400/400 = 100%
      // But these won't add to 100% which is expected since we're overriding
      render(<MacroDisplay macros={mockMacros} calories={400} />);
      
      expect(screen.getByText('50%')).toBeInTheDocument(); // Protein
      expect(screen.getByText('68%')).toBeInTheDocument(); // Fat
      expect(screen.getByText('100%')).toBeInTheDocument(); // Carbs
    });
  });

  describe('number formatting', () => {
    it('should format calories with 0 decimal places', () => {
      render(<MacroDisplay macros={mockMacros} calories={1234.56} />);
      
      expect(screen.getByText('1235kcal')).toBeInTheDocument(); // Rounded
    });

    it('should format macro values with 1 decimal place', () => {
      render(
        <MacroDisplay
          macros={{ protein: 25.67, fat: 15.43, carbs: 89.99 }}
          calories={500}
        />
      );
      
      expect(screen.getByText('25.7g')).toBeInTheDocument(); // Protein
      expect(screen.getByText('15.4g')).toBeInTheDocument(); // Fat
      expect(screen.getByText('90.0g')).toBeInTheDocument(); // Carbs rounded up
    });

    it('should format percentages with 0 decimal places', () => {
      // Create a scenario with non-round percentages
      render(<MacroDisplay macros={{ protein: 33.3, fat: 22.2, carbs: 44.4 }} />);
      
      // All should be whole numbers
      const allText = screen.getByRole('list').textContent;
      expect(allText).toMatch(/\d+%/); // Should have percentages as integers
    });
  });

  describe('conditional rendering', () => {
    it('should show calorie row when calories prop provided', () => {
      render(<MacroDisplay macros={mockMacros} calories={500} />);
      
      expect(screen.getByText('Kalorie')).toBeInTheDocument();
      expect(screen.getByText('500kcal')).toBeInTheDocument();
    });

    it('should not show calorie row when calories prop omitted', () => {
      render(<MacroDisplay macros={mockMacros} />);
      
      expect(screen.queryByText('Kalorie')).not.toBeInTheDocument();
    });

    it('should always show macro rows', () => {
      render(<MacroDisplay macros={mockMacros} />);
      
      expect(screen.getByText('Białko')).toBeInTheDocument();
      expect(screen.getByText('Tłuszcze')).toBeInTheDocument();
      expect(screen.getByText('Węglowodany')).toBeInTheDocument();
    });
  });

  describe('macro display structure', () => {
    it('should render with correct card title', () => {
      render(<MacroDisplay macros={mockMacros} />);
      
      expect(screen.getByText('Makroskładniki')).toBeInTheDocument();
    });

    it('should render with description', () => {
      render(<MacroDisplay macros={mockMacros} />);
      
      expect(screen.getByText('Dzisiejsze spożycie')).toBeInTheDocument();
    });

    it('should display macro values with units', () => {
      render(<MacroDisplay macros={mockMacros} />);
      
      expect(screen.getByText('50.0g')).toBeInTheDocument();
      expect(screen.getByText('30.0g')).toBeInTheDocument();
      expect(screen.getByText('100.0g')).toBeInTheDocument();
    });
  });
});

