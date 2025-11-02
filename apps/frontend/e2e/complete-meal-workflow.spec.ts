/**
 * Complete E2E test scenario for meal tracking workflow
 *
 * Test scenario:
 * 1. Login to test account
 * 2. Change calorie goal
 * 3. Add breakfast meal
 * 4. Save the meal
 * 5. Add lunch meal
 * 6. Retry meal calculation
 * 7. Save the meal
 */

import { config } from 'dotenv';
import { test, expect } from './test';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { ProfilePage } from './pages/ProfilePage';
import { AddMealDialog } from './pages/AddMealDialog';

// Load environment variables from .env.test
config({ path: '.env.test' });

// Test credentials from environment variables
const TEST_EMAIL = process.env.E2E_USERNAME!;
const TEST_PASSWORD = process.env.E2E_PASSWORD!;
const NEW_CALORIE_GOAL = 2200;

  test.describe('Complete Meal Workflow', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;
  let profilePage: ProfilePage;
  let addMealDialog: AddMealDialog;

  test.beforeAll(async ({ supawright }) => {
    // Clean up any existing meals for the test user ONCE before all tests
    const { data: { user } } = await supawright.supabase().auth.getUser();
    if (user) {
      await supawright.supabase()
        .from('meals')
        .delete()
        .eq('user_id', user.id);
    }
  });

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    profilePage = new ProfilePage(page);
    addMealDialog = new AddMealDialog(page);
  });

  test('should complete full meal tracking workflow', async ({ page }) => {
    // Step 1: Login to test account
    await loginPage.goto();
    await loginPage.login(TEST_EMAIL, TEST_PASSWORD);
    await loginPage.waitForSuccessfulLogin();

    // Verify we're on dashboard
    await expect(dashboardPage.pageTitle).toBeVisible();

    // Step 2: Change calorie goal
    await dashboardPage.goToProfile();
    await expect(profilePage.pageTitle).toBeVisible();

    // Edit calorie goal
    await profilePage.startEditingCalorieGoal();
    await expect(profilePage.calorieGoalInput).toBeVisible();

    // Set new goal
    await profilePage.setCalorieGoal(NEW_CALORIE_GOAL);
    await profilePage.saveCalorieGoal();

    // Verify goal was updated (wait for save to complete)
    await page.waitForTimeout(process.env.CI ? 3000 : 1000);
    await expect(profilePage.calorieGoalInput).not.toBeVisible();

    // Go back to dashboard
    await dashboardPage.goto();
    await expect(dashboardPage.pageTitle).toBeVisible();

    // Step 3: Add breakfast meal
    await dashboardPage.startAddingMeal();
    await expect(addMealDialog.dialog).toBeVisible();
    await addMealDialog.waitForInputStep();

    // Select breakfast category and enter description
    await addMealDialog.selectCategory('kolacja');
    await addMealDialog.enterDescription('2 jajka na twardo, kromka chleba z masłem, szklanka mleka');

    // Step 4: Save the meal (submit for analysis)
    await addMealDialog.submit();

    // Wait for analysis loading
    await addMealDialog.waitForLoadingStep();
    await expect(addMealDialog.analysisLoadingCancel).toBeVisible();

    // Wait for analysis to complete (results step)
    await addMealDialog.waitForResultsStep();
    await expect(addMealDialog.resultsAcceptButton).toBeVisible();

    // Verify analysis results
    await expect(addMealDialog.resultsMacroDisplay).toBeVisible();
    await expect(addMealDialog.resultsIngredientsTable).toBeVisible();
    await expect(addMealDialog.hasIngredients()).toBeTruthy();

    // Step 5: Accept and save breakfast
    await addMealDialog.acceptResults();

    // Wait for dialog to close and dashboard to update
    await expect(addMealDialog.dialog).not.toBeVisible();
    await page.waitForTimeout(process.env.CI ? 5000 : 2000);

    // Refresh dashboard data to show the new meal
    await dashboardPage.refresh();
    await page.waitForTimeout(process.env.CI ? 5000 : 2000);

    // Verify meal was added to dashboard
    await expect(dashboardPage.mealsList).toBeVisible();

    // Debug: check what's happening with getMealsCount
    console.log('Checking meals count...');
    const mealsCount = await dashboardPage.getMealsCount();
    console.log('Meals count result:', mealsCount, typeof mealsCount);
    await expect(mealsCount).toBeGreaterThan(0);

    // Step 6: Add lunch meal
    await dashboardPage.startAddingMeal();
    await expect(addMealDialog.dialog).toBeVisible();
    await addMealDialog.waitForInputStep();

    // Select lunch category and enter description
    await addMealDialog.selectCategory('obiad');
    await addMealDialog.enterDescription('Grillowana pierś kurczaka 150g, ryż 100g, mieszanka warzywna 200g');

    // Submit for analysis
    await addMealDialog.submit();

    // Wait for analysis loading
    await addMealDialog.waitForLoadingStep();
    await addMealDialog.waitForResultsStep();

    // Step 7: Retry meal calculation
    await addMealDialog.retryAnalysis();

    // Wait for loading again
    await addMealDialog.waitForLoadingStep();
    await addMealDialog.waitForResultsStep();

    // Verify results again
    await expect(addMealDialog.resultsMacroDisplay).toBeVisible();
    await expect(addMealDialog.hasIngredients()).toBeTruthy();

    // Step 8: Save the lunch meal
    await addMealDialog.acceptResults();

    // Wait for dialog to close
    await expect(addMealDialog.dialog).not.toBeVisible();
    await page.waitForTimeout(process.env.CI ? 5000 : 2000);

    // Refresh dashboard data to show the new meal
    await dashboardPage.refresh();
    await page.waitForTimeout(process.env.CI ? 5000 : 2000);

    // Final verification - should have 2 meals now
    await expect(mealsCount).toBeGreaterThan(1);

    // Verify total calories are displayed and updated
    await expect(dashboardPage.caloriesDisplay).toBeVisible();
    const currentCalories = await dashboardPage.getCurrentCalories();
    await expect(currentCalories).toBeGreaterThan(0);

    // Take screenshot for verification
    await dashboardPage.screenshot('final-meal-workflow');
  });

  test('should handle manual calorie entry', async ({ page }) => {
    // Login first
    await loginPage.goto();
    await loginPage.login(TEST_EMAIL, TEST_PASSWORD);
    await loginPage.waitForSuccessfulLogin();

    // Start adding meal
    await dashboardPage.startAddingMeal();
    await expect(addMealDialog.dialog).toBeVisible();
    await addMealDialog.waitForInputStep();

    // Select category
    await addMealDialog.selectCategory('śniadanie');

    // Enable manual mode
    await addMealDialog.toggleManualMode();
    await expect(addMealDialog.isManualMode()).toBeTruthy();

    // Enter calories manually
    await addMealDialog.enterCalories(450);
    await addMealDialog.submit();

    // Should go directly to success (no analysis needed for manual mode)
    await expect(addMealDialog.dialog).not.toBeVisible();

    // Verify meal was added
    await page.waitForTimeout(process.env.CI ? 5000 : 2000);
    const mealsCount = await dashboardPage.getMealsCount();
    await expect(mealsCount).toBeGreaterThan(0);
  });

  test('should handle calorie goal validation', async ({ page }) => {
    // Login first
    await loginPage.goto();
    await loginPage.login(TEST_EMAIL, TEST_PASSWORD);
    await loginPage.waitForSuccessfulLogin();

    // Go to profile
    await dashboardPage.goToProfile();
    await expect(profilePage.pageTitle).toBeVisible();

    // Try to set invalid calorie goal
    await profilePage.startEditingCalorieGoal();
    await profilePage.setCalorieGoal(-100);
    await profilePage.saveCalorieGoal();

    // Should show error
    await expect(await profilePage.hasCalorieGoalError()).toBeTruthy();
    const errorMessage = await profilePage.getCalorieGoalError();
    await expect(errorMessage).toContain('Cel musi być liczbą większą od 0');

    // Cancel editing
    await profilePage.cancelCalorieGoal();

    // Wait for edit mode to be cancelled
    await page.waitForTimeout(process.env.CI ? 3000 : 1500);
    await expect(await profilePage.isInEditMode()).toBeFalsy();
  });
});
