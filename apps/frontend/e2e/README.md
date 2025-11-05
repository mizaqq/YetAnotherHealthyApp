# E2E Tests with Playwright

This directory contains end-to-end tests for the YetAnotherHealthyApp using Playwright framework.

## Test Structure

```
e2e/
├── pages/                    # Page Object Models
│   ├── LoginPage.ts         # Login page interactions
│   ├── DashboardPage.ts     # Dashboard page interactions
│   ├── ProfilePage.ts       # Profile page interactions
│   └── AddMealDialog.ts     # Add meal dialog interactions
├── complete-meal-workflow.spec.ts # Complete user workflow test
├── auth.spec.ts             # Authentication tests
└── README.md               # This file
```

## Test Scenarios

### Complete Meal Workflow

The main test scenario covers:

1. **Login** to test account
2. **Change calorie goal** in profile settings
3. **Add breakfast meal** with AI analysis
4. **Save the meal** after analysis
5. **Add lunch meal** with retry functionality
6. **Retry meal calculation** to demonstrate error handling
7. **Save the meal** and verify dashboard updates

### Additional Test Cases

- **Manual calorie entry**: Test manual mode without AI analysis
- **Calorie goal validation**: Test form validation for invalid inputs

## Data Attributes (data-testid)

All interactive elements have been tagged with `data-testid` attributes for reliable test automation:

### Authentication Components

- `auth-email-input` - Email input field
- `auth-password-input` - Password input field
- `auth-password-toggle` - Password visibility toggle
- `auth-submit` - Login/Register submit button
- `auth-api-error` - API error message
- `auth-forgot-password-link` - Forgot password link
- `auth-switch-mode-link` - Switch between login/register

### Dashboard Components

- `add-meal-fab` - Floating action button to add meals
- `dashboard-calorie-display` - Current calories display
- `dashboard-progress-display` - Progress bar component
- `dashboard-meals-list` - List of today's meals
- `dashboard-macro-display` - Macronutrients display
- `dashboard-weekly-chart` - Weekly trend chart

### Profile Components

- `calorie-goal-edit-button` - Edit calorie goal button
- `calorie-goal-input` - Calorie goal input field
- `calorie-goal-save-button` - Save calorie goal button
- `calorie-goal-cancel-button` - Cancel editing button
- `calorie-goal-error` - Validation error message
- `profile-logout-button` - Logout button

### Add Meal Components

- `add-meal-dialog-close` - Dialog close button
- `add-meal-error-message` - General error message
- `meal-input-form` - Meal input form
- `meal-category-dropdown` - Meal category selection
- `meal-manual-mode-switch` - Manual/AI mode toggle
- `meal-description-textarea` - Meal description input
- `meal-calories-input` - Manual calories input
- `meal-input-submit` - Submit button
- `analysis-loading-cancel` - Cancel during AI analysis
- `analysis-results-error-message` - Analysis error message
- `analysis-results-macro-display` - Analysis results macros
- `analysis-results-ingredients-table` - Ingredients table
- `analysis-results-cancel` - Cancel from results
- `analysis-results-retry` - Retry analysis button
- `analysis-results-accept` - Accept and save results

## Running Tests

### Prerequisites

1. **Environment Setup**: Copy `.env.test` and configure your Supabase credentials and test user:

   ```bash
   cp .env.test .env.test.local
   # Edit .env.test.local with your actual values
   ```

2. **Start the development server**: `npm run dev`
3. **Start the backend API**: `cd ../backend && python -m uvicorn app.main:app --reload`
4. **Ensure test database is available** and test user exists

### Run All Tests

```bash
npm run test:e2e
```

### Run Specific Test

```bash
npx playwright test complete-meal-workflow.spec.ts
```

### Run Tests in Debug Mode

```bash
npx playwright test complete-meal-workflow.spec.ts --debug
```

### View Test Reports

```bash
npx playwright show-report
```

## Page Object Model

All tests use the Page Object Model pattern for maintainability:

- **LoginPage**: Handles authentication flows
- **DashboardPage**: Main dashboard interactions and verifications
- **ProfilePage**: Profile settings and calorie goal management
- **AddMealDialog**: Complete meal addition workflow

Each page object encapsulates:

- Element locators using `data-testid` attributes
- User actions (clicks, typing, navigation)
- Verification methods (assertions, data extraction)
- Wait conditions for dynamic content

## Best Practices

1. **Use data-testid**: All new interactive elements should include `data-testid` attributes
2. **Page Object Model**: Keep test logic in page objects, not in test files
3. **Semantic locators**: Use `getByRole()`, `getByLabel()`, `getByText()` when possible
4. **Wait strategies**: Use `waitFor()` methods instead of arbitrary timeouts
5. **Assertions**: Use specific matchers for better error messages
6. **Screenshots**: Capture screenshots on failures for debugging

## Test Data

Test credentials and configuration are stored in `.env.test`:

- `VITE_SUPABASE_URL` - Supabase project URL for testing
- `VITE_SUPABASE_ANON_KEY` - Supabase anonymous key for testing
- `E2E_USERNAME_ID` - Test user ID (optional)
- `E2E_USERNAME` - Test user email
- `E2E_PASSWORD` - Test user password
- `API_BASE_URL` - Backend API URL

Environment variables are automatically loaded using `dotenv` in the test files.

## Test Configuration

Tests automatically load configuration from `.env.test` file:

- **Supabase Settings**: Used for authentication and database connections
- **Test User**: Pre-configured user for testing (should exist in your Supabase instance)
- **API Endpoints**: Backend API URL for API testing
- **Timeouts**: Configurable test timeouts and retry counts

## Continuous Integration

Tests are configured to:

- Run in parallel for faster execution
- Retry failed tests on CI environments
- Capture screenshots and videos on failures
- Generate HTML reports for easy review

## Adding New Tests

1. Create test file in `e2e/` directory
2. Use existing page objects or create new ones
3. Add `data-testid` attributes to new components
4. Follow the 'Arrange, Act, Assert' pattern
5. Include meaningful assertions and error messages

## Environment Variables Reference

| Variable                                     | Description            | Required | Example                            |
| -------------------------------------------- | ---------------------- | -------- | ---------------------------------- |
| `REACT_APP_SUPABASE_URL`                     | Supabase project URL   | Yes      | `https://your-project.supabase.co` |
| `REACT_APP_SUPABASE_PUBLISHABLE_DEFAULT_KEY` | Supabase anonymous key | Yes      | `eyJ...`                           |
| `E2E_USERNAME_ID`                            | Test user ID           | No       | `test-user-123`                    |
| `E2E_USERNAME`                               | Test user email        | Yes      | `test@example.com`                 |
| `E2E_PASSWORD`                               | Test user password     | Yes      | `secure-password`                  |
| `API_BASE_URL`                               | Backend API URL        | No       | `http://localhost:8000`            |
