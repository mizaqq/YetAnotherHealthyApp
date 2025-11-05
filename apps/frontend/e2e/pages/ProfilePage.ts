/**
 * Page Object Model for Profile Page
 */

import { Page, Locator } from '@playwright/test';

export class ProfilePage {
  readonly page: Page;
  readonly pageTitle: Locator;
  readonly emailField: Locator;
  readonly calorieGoalEditButton: Locator;
  readonly calorieGoalInput: Locator;
  readonly calorieGoalSaveButton: Locator;
  readonly calorieGoalCancelButton: Locator;
  readonly calorieGoalError: Locator;
  readonly logoutButton: Locator;

  constructor(page: Page) {
    this.page = page;

    // Define locators using data-testid for reliable testing
    this.pageTitle = page.getByRole('heading', { name: /profil/i });
    this.emailField = page.getByText(/email/i);
    this.calorieGoalEditButton = page.getByTestId('calorie-goal-edit-button');
    this.calorieGoalInput = page.getByTestId('calorie-goal-input');
    this.calorieGoalSaveButton = page.getByTestId('calorie-goal-save-button');
    this.calorieGoalCancelButton = page.getByTestId('calorie-goal-cancel-button');
    this.calorieGoalError = page.getByTestId('calorie-goal-error');
    this.logoutButton = page.getByTestId('profile-logout-button');
  }

  /**
   * Navigate to the profile page
   */
  async goto() {
    await this.page.goto('/profile');
  }

  /**
   * Check if user is on profile page
   */
  async isOnProfile() {
    await this.pageTitle.waitFor({ state: 'visible' });
    return await this.page.url().includes('/profile');
  }

  /**
   * Start editing calorie goal
   */
  async startEditingCalorieGoal() {
    await this.calorieGoalEditButton.click();
  }

  /**
   * Set new calorie goal value
   */
  async setCalorieGoal(value: number) {
    await this.calorieGoalInput.fill(value.toString());
  }

  /**
   * Save calorie goal changes
   */
  async saveCalorieGoal() {
    await this.calorieGoalSaveButton.click();
  }

  /**
   * Cancel calorie goal editing
   */
  async cancelCalorieGoal() {
    await this.calorieGoalCancelButton.click();
  }

  /**
   * Get current calorie goal value
   */
  async getCurrentCalorieGoal() {
    const text = await this.page.getByText(/\d+ kcal/).textContent();
    const match = text?.match(/(\d+)/);
    return match ? parseInt(match[1], 10) : 0;
  }

  /**
   * Check if calorie goal error is visible
   */
  async hasCalorieGoalError() {
    return await this.calorieGoalError.isVisible();
  }

  /**
   * Get calorie goal error message
   */
  async getCalorieGoalError() {
    return await this.calorieGoalError.textContent();
  }

  /**
   * Logout from profile
   */
  async logout() {
    await this.logoutButton.click();
  }

  /**
   * Check if in edit mode (input field visible)
   */
  async isInEditMode() {
    try {
      const count = await this.calorieGoalInput.count();
      return count > 0;
    } catch {
      return false;
    }
  }
}
