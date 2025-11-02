/**
 * Page Object Model for Add Meal Dialog
 */

import { Page, Locator } from '@playwright/test';

export class AddMealDialog {
  readonly page: Page;
  readonly dialog: Locator;
  readonly closeButton: Locator;
  readonly errorMessage: Locator;
  readonly mealInputForm: Locator;
  readonly categoryDropdown: Locator;
  readonly manualModeSwitch: Locator;
  readonly descriptionTextarea: Locator;
  readonly caloriesInput: Locator;
  readonly submitButton: Locator;
  readonly analysisLoadingCancel: Locator;
  readonly analysisResultsError: Locator;
  readonly resultsMacroDisplay: Locator;
  readonly resultsIngredientsTable: Locator;
  readonly resultsCancelButton: Locator;
  readonly resultsRetryButton: Locator;
  readonly resultsAcceptButton: Locator;

  constructor(page: Page) {
    this.page = page;

    // Define locators using data-testid for reliable testing
    this.dialog = page.locator('[role="dialog"]');
    this.closeButton = page.getByTestId('add-meal-dialog-close');
    this.errorMessage = page.getByTestId('add-meal-error-message');
    this.mealInputForm = page.getByTestId('meal-input-form');
    this.categoryDropdown = page.getByTestId('meal-category-dropdown');
    this.manualModeSwitch = page.getByTestId('meal-manual-mode-switch');
    this.descriptionTextarea = page.getByTestId('meal-description-textarea');
    this.caloriesInput = page.getByTestId('meal-calories-input');
    this.submitButton = page.getByTestId('meal-input-submit');
    this.analysisLoadingCancel = page.getByTestId('analysis-loading-cancel');
    this.analysisResultsError = page.getByTestId('analysis-results-error-message');
    this.resultsMacroDisplay = page.getByTestId('analysis-results-macro-display');
    this.resultsIngredientsTable = page.getByTestId('analysis-results-ingredients-table');
    this.resultsCancelButton = page.getByTestId('analysis-results-cancel');
    this.resultsRetryButton = page.getByTestId('analysis-results-retry');
    this.resultsAcceptButton = page.getByTestId('analysis-results-accept');
  }

  /**
   * Check if dialog is visible
   */
  async isVisible() {
    return await this.dialog.isVisible();
  }

  /**
   * Close the dialog
   */
  async close() {
    await this.closeButton.click();
  }

  /**
   * Select meal category
   */
  async selectCategory(category: string) {
    await this.categoryDropdown.click();
    await this.page.getByRole('option', { name: new RegExp(category, 'i') }).click();
  }

  /**
   * Toggle manual mode
   */
  async toggleManualMode() {
    await this.manualModeSwitch.click();
  }

  /**
   * Check if in manual mode
   */
  async isManualMode() {
    return await this.manualModeSwitch.evaluate(el => (el as HTMLInputElement).checked);
  }

  /**
   * Enter meal description
   */
  async enterDescription(description: string) {
    await this.descriptionTextarea.fill(description);
  }

  /**
   * Enter calories in manual mode
   */
  async enterCalories(calories: number) {
    await this.caloriesInput.fill(calories.toString());
  }

  /**
   * Submit the meal form
   */
  async submit() {
    await this.submitButton.click();
  }

  /**
   * Cancel during analysis loading
   */
  async cancelLoading() {
    await this.analysisLoadingCancel.click();
  }

  /**
   * Accept analysis results
   */
  async acceptResults() {
    await this.resultsAcceptButton.click();
  }

  /**
   * Retry analysis
   */
  async retryAnalysis() {
    await this.resultsRetryButton.click();
  }

  /**
   * Cancel from results
   */
  async cancelResults() {
    await this.resultsCancelButton.click();
  }

  /**
   * Wait for input step to be visible
   */
  async waitForInputStep() {
    await this.mealInputForm.waitFor({ state: 'visible' });
  }

  /**
   * Wait for loading step to be visible
   */
  async waitForLoadingStep(timeout?: number) {
    const waitTimeout = timeout || (process.env.CI ? 15000 : 10000); // 15s on CI, 10s locally
    await this.analysisLoadingCancel.waitFor({ state: 'visible', timeout: waitTimeout });
  }

  /**
   * Wait for results step to be visible
   * Increased timeout for CI environments where API calls may be slower
   */
  async waitForResultsStep(timeout?: number) {
    const waitTimeout = timeout || (process.env.CI ? 60000 : 30000); // 60s on CI, 30s locally
    await this.resultsAcceptButton.waitFor({ state: 'visible', timeout: waitTimeout });
  }

  /**
   * Check if has error message
   */
  async hasError() {
    return await this.errorMessage.isVisible() || await this.analysisResultsError.isVisible();
  }

  /**
   * Get error message text
   */
  async getErrorMessage() {
    if (await this.errorMessage.isVisible()) {
      return await this.errorMessage.textContent();
    }
    if (await this.analysisResultsError.isVisible()) {
      return await this.analysisResultsError.textContent();
    }
    return '';
  }

  /**
   * Get calories from results
   */
  async getResultsCalories() {
    const caloriesText = await this.resultsMacroDisplay.getByText(/\d+ kcal/).textContent();
    const match = caloriesText?.match(/(\d+)/);
    return match ? parseInt(match[1], 10) : 0;
  }

  /**
   * Check if ingredients table has rows
   */
  async hasIngredients() {
    return await this.resultsIngredientsTable.locator('tbody tr').count() > 0;
  }
}
