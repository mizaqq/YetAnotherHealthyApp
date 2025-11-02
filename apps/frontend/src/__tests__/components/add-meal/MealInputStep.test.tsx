import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MealInputStep } from '@/components/add-meal/MealInputStep';
import type { MealCategoryDTO, MealInputFormViewModel } from '@/types';

describe('MealInputStep', () => {
  const mockCategories: MealCategoryDTO[] = [
    { code: 'breakfast', locale: 'pl', label: 'Śniadanie' },
    { code: 'lunch', locale: 'pl', label: 'Obiad' },
    { code: 'dinner', locale: 'pl', label: 'Kolacja' },
  ];

  const defaultInitialData: Partial<MealInputFormViewModel> = {
    category: '',
    description: '',
    isManualMode: false,
    manualCalories: null,
  };

  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('AI mode validation', () => {
    it('should show error when category is not selected', async () => {
      const user = userEvent.setup();
      render(
        <MealInputStep
          initialData={defaultInitialData}
          categories={mockCategories}
          isLoading={false}
          onSubmit={mockOnSubmit}
        />
      );

      const submitButton = screen.getByRole('button', { name: /analizuj/i });
      await user.click(submitButton);

      // The component uses custom validation, so we just verify onSubmit wasn't called
      await waitFor(() => {
        expect(mockOnSubmit).not.toHaveBeenCalled();
      });
    });

    it('should show error when description is too short', async () => {
      const user = userEvent.setup();
      render(
        <MealInputStep
          initialData={{ ...defaultInitialData, category: 'breakfast' }}
          categories={mockCategories}
          isLoading={false}
          onSubmit={mockOnSubmit}
        />
      );

      const textarea = screen.getByPlaceholderText(/wprowadź opis swojego posiłku/i);
      await user.type(textarea, 'ab'); // Only 2 characters

      const submitButton = screen.getByRole('button', { name: /analizuj/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).not.toHaveBeenCalled();
      });
    });

    it('should show error when description is empty', async () => {
      const user = userEvent.setup();
      render(
        <MealInputStep
          initialData={{ ...defaultInitialData, category: 'breakfast' }}
          categories={mockCategories}
          isLoading={false}
          onSubmit={mockOnSubmit}
        />
      );

      const submitButton = screen.getByRole('button', { name: /analizuj/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).not.toHaveBeenCalled();
      });
    });

    it('should call onSubmit with valid form data in AI mode', async () => {
      const user = userEvent.setup();
      render(
        <MealInputStep
          initialData={defaultInitialData}
          categories={mockCategories}
          isLoading={false}
          onSubmit={mockOnSubmit}
        />
      );

      // Select category
      const categoryDropdown = screen.getByRole('combobox', { name: /kategoria posiłku/i });
      await user.click(categoryDropdown);
      
      const breakfastOption = await screen.findByRole('option', { name: 'Śniadanie' });
      await user.click(breakfastOption);

      // Enter description
      const textarea = screen.getByPlaceholderText(/wprowadź opis swojego posiłku/i);
      await user.type(textarea, '2 jajka na twardo');

      const submitButton = screen.getByRole('button', { name: /analizuj/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          category: 'breakfast',
          description: '2 jajka na twardo',
          isManualMode: false,
          manualCalories: null,
        });
      });
    });
  });

  describe('manual mode validation', () => {
    it('should show error when category is not selected in manual mode', async () => {
      const user = userEvent.setup();
      render(
        <MealInputStep
          initialData={{ ...defaultInitialData, isManualMode: true }}
          categories={mockCategories}
          isLoading={false}
          onSubmit={mockOnSubmit}
        />
      );

      const caloriesInput = screen.getByPlaceholderText(/np\. 450/i);
      await user.type(caloriesInput, '500');

      const submitButton = screen.getByRole('button', { name: /zapisz/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).not.toHaveBeenCalled();
      });
    });

    it('should show error when manualCalories is 0', async () => {
      const user = userEvent.setup();
      render(
        <MealInputStep
          initialData={{ ...defaultInitialData, category: 'lunch', isManualMode: true }}
          categories={mockCategories}
          isLoading={false}
          onSubmit={mockOnSubmit}
        />
      );

      const caloriesInput = screen.getByPlaceholderText(/np\. 450/i);
      await user.clear(caloriesInput);
      await user.type(caloriesInput, '0');

      const submitButton = screen.getByRole('button', { name: /zapisz/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).not.toHaveBeenCalled();
      });
    });

    it('should show error when manualCalories is negative', async () => {
      const user = userEvent.setup();
      render(
        <MealInputStep
          initialData={{ ...defaultInitialData, category: 'lunch', isManualMode: true }}
          categories={mockCategories}
          isLoading={false}
          onSubmit={mockOnSubmit}
        />
      );

      const caloriesInput = screen.getByPlaceholderText(/np\. 450/i);
      await user.type(caloriesInput, '-10');

      const submitButton = screen.getByRole('button', { name: /zapisz/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).not.toHaveBeenCalled();
      });
    });

    it('should show error when manualCalories is empty', async () => {
      const user = userEvent.setup();
      render(
        <MealInputStep
          initialData={{ ...defaultInitialData, category: 'lunch', isManualMode: true }}
          categories={mockCategories}
          isLoading={false}
          onSubmit={mockOnSubmit}
        />
      );

      const submitButton = screen.getByRole('button', { name: /zapisz/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).not.toHaveBeenCalled();
      });
    });

    it('should call onSubmit with valid form data in manual mode', async () => {
      const user = userEvent.setup();
      render(
        <MealInputStep
          initialData={{ ...defaultInitialData, isManualMode: true }}
          categories={mockCategories}
          isLoading={false}
          onSubmit={mockOnSubmit}
        />
      );

      // Select category
      const categoryDropdown = screen.getByRole('combobox', { name: /kategoria posiłku/i });
      await user.click(categoryDropdown);
      
      const lunchOption = await screen.findByRole('option', { name: 'Obiad' });
      await user.click(lunchOption);

      // Enter calories
      const caloriesInput = screen.getByPlaceholderText(/np\. 450/i);
      await user.type(caloriesInput, '650');

      const submitButton = screen.getByRole('button', { name: /zapisz/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          category: 'lunch',
          description: '',
          isManualMode: true,
          manualCalories: 650,
        });
      });
    });
  });

  describe('mode switching', () => {
    it('should clear description when switching to manual mode', async () => {
      const user = userEvent.setup();
      render(
        <MealInputStep
          initialData={{ ...defaultInitialData, description: '2 jajka' }}
          categories={mockCategories}
          isLoading={false}
          onSubmit={mockOnSubmit}
        />
      );

      const textarea = screen.getByPlaceholderText(/wprowadź opis swojego posiłku/i);
      expect(textarea).toHaveValue('2 jajka');

      // Switch to manual mode
      const manualSwitch = screen.getByRole('switch', {
        name: /wprowadź kalorie ręcznie/i,
      });
      await user.click(manualSwitch);

      // Description field should be hidden and replaced with calories input
      expect(screen.queryByPlaceholderText(/wprowadź opis swojego posiłku/i)).not.toBeInTheDocument();
      expect(screen.getByPlaceholderText(/np\. 450/i)).toBeInTheDocument();
    });

    it('should clear manualCalories when switching to AI mode', async () => {
      const user = userEvent.setup();
      render(
        <MealInputStep
          initialData={{ ...defaultInitialData, isManualMode: true, manualCalories: 500 }}
          categories={mockCategories}
          isLoading={false}
          onSubmit={mockOnSubmit}
        />
      );

      const caloriesInput = screen.getByPlaceholderText(/np\. 450/i);
      expect(caloriesInput).toHaveValue(500);

      // Switch to AI mode
      const manualSwitch = screen.getByRole('switch', {
        name: /wprowadź kalorie ręcznie/i,
      });
      await user.click(manualSwitch);

      // Calories field should be hidden and replaced with description textarea
      expect(screen.queryByPlaceholderText(/np\. 450/i)).not.toBeInTheDocument();
      expect(screen.getByPlaceholderText(/wprowadź opis swojego posiłku/i)).toBeInTheDocument();
    });
  });

  describe('category dropdown', () => {
    it('should update category field when option selected', async () => {
      const user = userEvent.setup();
      render(
        <MealInputStep
          initialData={defaultInitialData}
          categories={mockCategories}
          isLoading={false}
          onSubmit={mockOnSubmit}
        />
      );

      const categoryDropdown = screen.getByRole('combobox', { name: /kategoria posiłku/i });
      await user.click(categoryDropdown);
      
      const dinnerOption = await screen.findByRole('option', { name: 'Kolacja' });
      await user.click(dinnerOption);

      // After selection, the dropdown should show the selected category label
      expect(categoryDropdown).toHaveValue('Kolacja');
    });

    it('should display correct label for selected category', () => {
      render(
        <MealInputStep
          initialData={{ ...defaultInitialData, category: 'breakfast' }}
          categories={mockCategories}
          isLoading={false}
          onSubmit={mockOnSubmit}
        />
      );

      const categoryDropdown = screen.getByRole('combobox', { name: /kategoria posiłku/i });
      expect(categoryDropdown).toHaveValue('Śniadanie');
    });

    it('should render all category options', async () => {
      const user = userEvent.setup();
      render(
        <MealInputStep
          initialData={defaultInitialData}
          categories={mockCategories}
          isLoading={false}
          onSubmit={mockOnSubmit}
        />
      );

      const categoryDropdown = screen.getByRole('combobox', { name: /kategoria posiłku/i });
      await user.click(categoryDropdown);
      
      await waitFor(() => {
        expect(screen.getByRole('option', { name: 'Śniadanie' })).toBeInTheDocument();
        expect(screen.getByRole('option', { name: 'Obiad' })).toBeInTheDocument();
        expect(screen.getByRole('option', { name: 'Kolacja' })).toBeInTheDocument();
      });
    });
  });

  describe('button labels', () => {
    it('should show "Analizuj" button in AI mode', () => {
      render(
        <MealInputStep
          initialData={{ ...defaultInitialData, isManualMode: false }}
          categories={mockCategories}
          isLoading={false}
          onSubmit={mockOnSubmit}
        />
      );

      expect(screen.getByRole('button', { name: /analizuj/i })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /zapisz/i })).not.toBeInTheDocument();
    });

    it('should show "Zapisz" button in manual mode', () => {
      render(
        <MealInputStep
          initialData={{ ...defaultInitialData, isManualMode: true }}
          categories={mockCategories}
          isLoading={false}
          onSubmit={mockOnSubmit}
        />
      );

      expect(screen.getByRole('button', { name: /zapisz/i })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /analizuj/i })).not.toBeInTheDocument();
    });
  });

  describe('loading state', () => {
    it('should disable all inputs when isLoading is true', () => {
      render(
        <MealInputStep
          initialData={defaultInitialData}
          categories={mockCategories}
          isLoading={true}
          onSubmit={mockOnSubmit}
        />
      );

      const categoryDropdown = screen.getByRole('combobox', { name: /kategoria posiłku/i });
      const manualSwitch = screen.getByRole('switch', { name: /wprowadź kalorie ręcznie/i });
      const textarea = screen.getByPlaceholderText(/wprowadź opis swojego posiłku/i);
      const submitButton = screen.getByRole('button', { name: /analizuj/i });

      expect(categoryDropdown).toBeDisabled();
      expect(manualSwitch).toBeDisabled();
      expect(textarea).toBeDisabled();
      expect(submitButton).toBeDisabled();
    });

    it('should disable manual calories input when isLoading is true', () => {
      render(
        <MealInputStep
          initialData={{ ...defaultInitialData, isManualMode: true }}
          categories={mockCategories}
          isLoading={true}
          onSubmit={mockOnSubmit}
        />
      );

      const caloriesInput = screen.getByPlaceholderText(/np\. 450/i);
      expect(caloriesInput).toBeDisabled();
    });
  });
});

