# Frontend Tests

This directory contains the test suite for the YetAnotherHealthyApp frontend built with React 19 and Vite.

## Test Structure

```
src/
├── __tests__/           # Test files
│   ├── components/      # Component tests
│   ├── hooks/          # Hook tests
│   └── utils/          # Utility function tests
├── setupTests.ts       # Global test setup
e2e/                    # E2E tests (Playwright)
├── pages/              # Page Object Models
│   ├── LoginPage.ts
│   └── DashboardPage.ts
├── auth.spec.ts        # Authentication E2E tests
└── example.spec.ts     # Example E2E tests
```

## Running Tests

### Install Dependencies

```bash
cd apps/frontend
npm install
```

### Unit Tests (Vitest)

```bash
# Run all unit tests once
npm test

# Run tests in watch mode (recommended during development)
npm run test:watch

# Run tests with UI mode
npm run test:ui

# Generate coverage report
npm run test:coverage
```

### E2E Tests (Playwright)

```bash
# Install Playwright browsers (first time only)
npx playwright install chromium

# Run E2E tests
npm run test:e2e

# Run E2E tests in UI mode
npm run test:e2e:ui

# Generate test code using codegen
npm run test:e2e:codegen

# View last test report
npm run test:e2e:report
```

## Writing Tests

### Component Tests

Use React Testing Library to test components from a user's perspective:

```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Button } from "./Button";

test("button handles click", async () => {
  const handleClick = vi.fn();
  const user = userEvent.setup();

  render(<Button onClick={handleClick}>Click me</Button>);

  await user.click(screen.getByRole("button"));
  expect(handleClick).toHaveBeenCalled();
});
```

### Hook Tests

Use `renderHook` to test custom hooks:

```tsx
import { renderHook, act } from "@testing-library/react";
import { useCounter } from "./useCounter";

test("increments counter", () => {
  const { result } = renderHook(() => useCounter());

  act(() => {
    result.current.increment();
  });

  expect(result.current.count).toBe(1);
});
```

### Utility Function Tests

Test pure functions directly:

```tsx
import { formatDate } from "./utils";

test("formats date correctly", () => {
  const date = new Date("2025-10-25");
  expect(formatDate(date)).toBe("2025-10-25");
});
```

### E2E Tests with Page Object Model

Use the Page Object Model pattern for maintainable E2E tests:

```tsx
import { test, expect } from "@playwright/test";
import { LoginPage } from "./pages/LoginPage";

test("user can login", async ({ page }) => {
  const loginPage = new LoginPage(page);

  await loginPage.goto();
  await loginPage.login("user@example.com", "password");

  await expect(page).toHaveURL("/dashboard");
});
```

## Vitest Patterns

### Mocking with vi

```tsx
// Mock a function
const mockFn = vi.fn();

// Mock a module
vi.mock("./api", () => ({
  fetchData: vi.fn(() => Promise.resolve({ data: "mocked" })),
}));

// Spy on a method
const spy = vi.spyOn(console, "log");
```

### Snapshot Testing

```tsx
expect(data).toMatchInlineSnapshot(`
  {
    "name": "Test",
    "value": 42,
  }
`);
```

### Parameterized Tests

```tsx
test.each([
  { input: 1, expected: 2 },
  { input: 2, expected: 4 },
  { input: 3, expected: 6 },
])("doubles $input to $expected", ({ input, expected }) => {
  expect(input * 2).toBe(expected);
});
```

## Playwright Patterns

### Locators

Use semantic locators for resilient tests:

```tsx
// By role (preferred)
page.getByRole("button", { name: /submit/i });

// By label
page.getByLabel("Email");

// By text
page.getByText("Welcome");

// By test ID (use sparingly)
page.getByTestId("submit-button");
```

### Assertions

```tsx
await expect(page.getByText("Success")).toBeVisible();
await expect(page).toHaveURL("/dashboard");
await expect(page).toHaveTitle(/Dashboard/);
```

### Visual Testing

```tsx
await expect(page).toHaveScreenshot("login-page.png");
```

### API Testing

```tsx
const response = await request.get("/api/v1/health");
expect(response.ok()).toBeTruthy();
```

## Available Test Utilities

### Vitest Globals

- `describe` / `test` / `it` - Test organization
- `expect` - Assertions
- `vi` - Mocking utilities
- `beforeEach` / `afterEach` - Test hooks
- `beforeAll` / `afterAll` - Suite hooks

### Testing Library

- `render` - Render components
- `screen` - Query rendered output
- `fireEvent` - Trigger events (use userEvent instead)
- `userEvent` - Simulate user interactions
- `waitFor` - Wait for async changes
- `renderHook` - Test custom hooks

### Custom Matchers (from @testing-library/jest-dom)

- `toBeInTheDocument()`
- `toBeVisible()`
- `toBeDisabled()`
- `toHaveTextContent()`
- `toHaveValue()`
- And many more...

## Best Practices

### Unit Tests

1. **Test behavior, not implementation**: Focus on what the component does, not how
2. **Use semantic queries**: Prefer `getByRole` over `getByTestId`
3. **Avoid testing internals**: Don't test state or props directly
4. **Keep tests isolated**: Each test should be independent
5. **Use userEvent**: Prefer `userEvent` over `fireEvent` for realistic interactions
6. **Mock external dependencies**: Mock API calls and external services
7. **Test accessibility**: Ensure components are accessible

### E2E Tests

1. **Use Page Object Model**: Encapsulate page logic in POM classes
2. **Test critical paths**: Focus on important user journeys
3. **Keep tests independent**: Each test should set up its own state
4. **Use semantic locators**: Avoid CSS selectors; use roles and labels
5. **Handle async properly**: Use Playwright's auto-waiting
6. **Run on Chromium only**: As per project guidelines
7. **Use visual regression**: For UI consistency checks

## Configuration

### Vitest (vitest.config.ts)

- **Environment**: jsdom for DOM testing
- **Coverage**: v8 provider with 60% thresholds
- **Setup**: Global setup in `src/setupTests.ts`

### Playwright (playwright.config.ts)

- **Browser**: Chromium only (Desktop Chrome)
- **Base URL**: http://localhost:5173
- **Traces**: On first retry
- **Screenshots**: On failure
- **Parallel**: Enabled for faster execution

## Debugging

### Vitest

```bash
# Run specific test file
npm test -- Button.test.tsx

# Run tests matching pattern
npm test -- -t "handles click"

# UI mode for visual debugging
npm run test:ui
```

### Playwright

```bash
# Debug mode (opens browser)
npx playwright test --debug

# Run specific test
npx playwright test auth.spec.ts

# Show trace viewer
npx playwright show-trace trace.zip

# View last report
npm run test:e2e:report
```

## Coverage

View coverage reports after running with `--coverage`:

```bash
npm run test:coverage
open coverage/index.html
```

Coverage thresholds are set in `vitest.config.ts`:

- Lines: 60%
- Functions: 60%
- Branches: 60%
- Statements: 60%

## CI/CD Integration

Tests run automatically in CI/CD pipeline. Ensure:

1. All unit tests pass
2. E2E tests pass
3. Coverage thresholds are met
4. No linting errors
5. TypeScript compiles without errors

## Common Issues

### Module Resolution

If imports fail, check `vitest.config.ts` alias configuration matches `tsconfig.json`.

### DOM Not Available

Ensure test file is recognized by Vitest and `environment: 'jsdom'` is set in config.

### Async Issues

Use `waitFor` for async operations:

```tsx
await waitFor(() => {
  expect(screen.getByText("Loaded")).toBeInTheDocument();
});
```

### Playwright Browser Not Found

Run `npx playwright install chromium` to install browsers.

### Port Already in Use

If dev server fails to start, ensure port 5173 is available or change in `playwright.config.ts`.

## Resources

- [Vitest documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Playwright documentation](https://playwright.dev/)
- [Testing Library queries](https://testing-library.com/docs/queries/about)
- [User Event](https://testing-library.com/docs/user-event/intro)
- [jest-dom matchers](https://github.com/testing-library/jest-dom)
