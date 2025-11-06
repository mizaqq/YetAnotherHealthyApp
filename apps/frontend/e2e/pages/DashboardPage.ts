/**
 * Page Object Model for Dashboard Page
 */

import { Page, Locator } from '@playwright/test';

export class DashboardPage {
  readonly page: Page;
  readonly pageTitle: Locator;
  readonly addMealButton: Locator;
  readonly caloriesDisplay: Locator;
  readonly progressDisplay: Locator;
  readonly mealsList: Locator;
  readonly macroDisplay: Locator;
  readonly weeklyChart: Locator;
  readonly profileLink: Locator;

  constructor(page: Page) {
    this.page = page;

    // Define locators using data-testid for reliable testing
    this.pageTitle = page.getByRole('heading', { name: /dzisiaj/i });
    this.addMealButton = page.getByTestId('add-meal-fab');
    this.caloriesDisplay = page.getByTestId('dashboard-calorie-display');
    this.progressDisplay = page.getByTestId('dashboard-progress-display');
    this.mealsList = page.getByTestId('dashboard-meals-list');
    this.macroDisplay = page.getByTestId('dashboard-macro-display');
    this.weeklyChart = page.getByTestId('dashboard-weekly-chart');
    this.profileLink = page.getByTestId('nav-profile');
  }

  /**
   * Navigate to the dashboard
   */
  async goto() {
    await this.page.goto('/');
  }

  /**
   * Check if user is on dashboard
   */
  async isOnDashboard() {
    await this.pageTitle.waitFor({ state: 'visible' });
    return await this.page.url().includes('/dashboard');
  }

  /**
   * Start adding a new meal
   */
  async startAddingMeal() {
    await this.addMealButton.click();
  }

  /**
   * Navigate to profile page
   */
  async goToProfile() {
    await this.profileLink.click();
  }

  /**
   * Get current calorie value from display
   */
  async getCurrentCalories() {
    const caloriesElement = this.caloriesDisplay.getByText('Spożyte kalorie').locator('..').getByText(/\d+/);
    const caloriesText = await caloriesElement.textContent();
    return caloriesText ? parseInt(caloriesText.replace(/\D/g, ''), 10) : 0;
  }

  /**
   * Get goal calories from display
   */
  async getGoalCalories() {
    const goalElement = this.caloriesDisplay.getByText('Cel dzienny').locator('..').getByText(/\d+/);
    const goalText = await goalElement.textContent();
    return goalText ? parseInt(goalText.replace(/\D/g, ''), 10) : 0;
  }

  /**
   * Check if meals list is empty
   */
  async isMealsListEmpty() {
    const emptyState = this.page.getByText(/nie dodałeś jeszcze posiłku/i);
    return await emptyState.isVisible();
  }

  /**
   * Get number of meals in the list
   */
  async getMealsCount() {
    try {
      // Check if meals list exists first
      const mealsListExists = await this.mealsList.isVisible();
      if (!mealsListExists) {
        console.log('Meals list is not visible');
        return 0;
      }

      // Try to count meal items
      const mealItems = this.page.locator('[data-testid^="meal-list-item-"]');
      const count = await mealItems.count();
      console.log(`Found ${count} meal items`);
      return count;
    } catch (error) {
      console.error('Error in getMealsCount:', error);
      return 0;
    }
  }

  /**
   * Click on a specific meal item
   */
  async clickMealItem(mealId: string) {
    await this.page.getByTestId(`meal-list-item-${mealId}`).click();
  }

  /**
   * Check if macro display shows specific values
   */
  async hasMacroValues(protein: number, fat: number, carbs: number) {
    const proteinText = await this.macroDisplay.getByText(`B: ${protein}`).isVisible();
    const fatText = await this.macroDisplay.getByText(`T: ${fat}`).isVisible();
    const carbsText = await this.macroDisplay.getByText(`W: ${carbs}`).isVisible();
    return proteinText && fatText && carbsText;
  }

  /**
   * Refresh dashboard data by navigating to the current page
   */
  async refresh() {
    await this.page.reload();
  }

  /**
   * Take a screenshot of the dashboard
   */
  async screenshot(name: string) {
    await this.page.screenshot({ path: `screenshots/${name}.png`, fullPage: true });
  }
}

