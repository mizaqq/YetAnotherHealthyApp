/**
 * Page Object Model for Login Page
 * 
 * This demonstrates the Page Object Model pattern for maintaining
 * E2E tests. Each page has its own class that encapsulates the
 * locators and actions specific to that page.
 */

import { Page, Locator } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly passwordToggle: Locator;
  readonly loginButton: Locator;
  readonly errorMessage: Locator;
  readonly forgotPasswordLink: Locator;
  readonly switchModeLink: Locator;

  constructor(page: Page) {
    this.page = page;

    // Define locators using data-testid for reliable testing
    this.emailInput = page.getByTestId('auth-email-input');
    this.passwordInput = page.getByTestId('auth-password-input');
    this.passwordToggle = page.getByTestId('auth-password-toggle');
    this.loginButton = page.getByTestId('auth-submit');
    this.errorMessage = page.getByTestId('auth-api-error');
    this.forgotPasswordLink = page.getByTestId('auth-forgot-password-link');
    this.switchModeLink = page.getByTestId('auth-switch-mode-link');
  }

  /**
   * Navigate to the login page
   */
  async goto() {
    await this.page.goto('/login');
  }

  /**
   * Perform login with credentials
   */
  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.loginButton.click();
  }

  /**
   * Wait for navigation after successful login
   */
  async waitForSuccessfulLogin() {
    // Wait for navigation away from login page
    await this.page.waitForURL(/^(?!.*\/auth\/login).*$/);
  }

  /**
   * Check if error message is visible
   */
  async hasError() {
    return await this.errorMessage.isVisible();
  }

  /**
   * Get error message text
   */
  async getErrorMessage() {
    return await this.errorMessage.textContent();
  }

  /**
   * Navigate to sign up page
   */
  async goToSignUp() {
    await this.switchModeLink.click();
  }

  /**
   * Toggle password visibility
   */
  async togglePasswordVisibility() {
    await this.passwordToggle.click();
  }

  /**
   * Navigate to forgot password page
   */
  async goToForgotPassword() {
    await this.forgotPasswordLink.click();
  }

  /**
   * Check if password is visible (input type is text)
   */
  async isPasswordVisible() {
    return await this.passwordInput.evaluate(el => (el as HTMLInputElement).type === 'text');
  }
}

