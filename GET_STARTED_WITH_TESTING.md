# Get Started with Testing

This guide will help you quickly set up and start testing in YetAnotherHealthyApp.

## 🚀 Quick Setup

### Step 1: Backend Testing Setup

```bash
# Navigate to backend
cd apps/backend

# Install test dependencies using uv
uv sync --group test

# Verify installation by running example tests
pytest

# You should see tests passing ✅
```

### Step 2: Frontend Testing Setup

```bash
# Navigate to frontend
cd apps/frontend

# Install all dependencies (including test packages)
npm install

# Install Playwright browsers
npx playwright install chromium

# Verify Vitest installation
npm test

# Verify Playwright installation
npm run test:e2e
```

## ✅ Verification

After setup, verify everything works:

### Backend

```bash
cd apps/backend
pytest -v
```

Expected output:

```
tests/unit/test_example_service.py::test_addition PASSED
tests/unit/test_example_service.py::test_square_numbers[0-0] PASSED
...
tests/integration/test_example_api.py::test_health_check_sync PASSED
```

### Frontend Unit Tests

```bash
cd apps/frontend
npm test
```

Expected output:

```
✓ src/__tests__/components/Button.test.tsx (4)
✓ src/__tests__/hooks/useCounter.test.ts (8)
✓ src/__tests__/utils/helpers.test.ts (7)
```

### Frontend E2E Tests

```bash
cd apps/frontend
npm run test:e2e
```

Expected output:

```
Running 10 tests using 1 worker
  ✓ [chromium] › auth.spec.ts:6:3 › should display login form
  ✓ [chromium] › example.spec.ts:8:3 › homepage loads successfully
```

## 📚 What Was Installed

### Backend Dependencies (`apps/backend/pyproject.toml`)

- ✅ `pytest` - Test framework
- ✅ `pytest-cov` - Code coverage
- ✅ `pytest-asyncio` - Async test support
- ✅ `respx` - HTTP request mocking

### Frontend Dependencies (`apps/frontend/package.json`)

- ✅ `vitest` - Unit test framework
- ✅ `@vitest/ui` - UI mode for tests
- ✅ `jsdom` - DOM environment
- ✅ `@testing-library/react` - React testing utilities
- ✅ `@testing-library/jest-dom` - Custom matchers
- ✅ `@testing-library/user-event` - User interaction simulation
- ✅ `@vitest/coverage-v8` - Code coverage
- ✅ `@playwright/test` - E2E testing framework

## 📁 Test Structure Created

```
apps/
├── backend/
│   └── tests/
│       ├── conftest.py          # Shared fixtures
│       ├── unit/                # Unit tests
│       │   ├── __init__.py
│       │   └── test_example_service.py
│       ├── integration/         # Integration tests
│       │   ├── __init__.py
│       │   └── test_example_api.py
│       └── README.md            # Backend testing docs
│
└── frontend/
    ├── src/
    │   ├── __tests__/           # Unit tests
    │   │   ├── components/
    │   │   │   └── Button.test.tsx
    │   │   ├── hooks/
    │   │   │   └── useCounter.test.ts
    │   │   └── utils/
    │   │       └── helpers.test.ts
    │   └── setupTests.ts        # Test setup
    ├── e2e/                     # E2E tests
    │   ├── pages/               # Page Object Models
    │   │   ├── LoginPage.ts
    │   │   └── DashboardPage.ts
    │   ├── auth.spec.ts
    │   └── example.spec.ts
    ├── vitest.config.ts         # Vitest config
    ├── playwright.config.ts     # Playwright config
    └── tests/
        └── README.md            # Frontend testing docs
```

## 🎯 Next Steps

### 1. Write Your First Backend Test

Create a test for an existing service:

```bash
cd apps/backend/tests/unit
touch test_meal_service.py
```

```python
# test_meal_service.py
import pytest
from app.services.meal_service import MealService

def test_meal_creation():
    # Your test here
    pass
```

### 2. Write Your First Frontend Component Test

Create a test for an existing component:

```bash
cd apps/frontend/src/__tests__/components
touch AddMealForm.test.tsx
```

```tsx
// AddMealForm.test.tsx
import { render, screen } from "@testing-library/react";
import { AddMealForm } from "../../components/add-meal/AddMealForm";

test("renders meal form", () => {
  render(<AddMealForm />);
  expect(screen.getByRole("form")).toBeInTheDocument();
});
```

### 3. Write Your First E2E Test

Create a new E2E test:

```bash
cd apps/frontend/e2e
touch dashboard.spec.ts
```

```tsx
// dashboard.spec.ts
import { test, expect } from "@playwright/test";
import { DashboardPage } from "./pages/DashboardPage";

test("dashboard displays correctly", async ({ page }) => {
  const dashboardPage = new DashboardPage(page);
  await dashboardPage.goto();

  await expect(dashboardPage.pageTitle).toBeVisible();
});
```

## 💡 Development Workflow

### Backend Development

```bash
cd apps/backend

# Run tests in watch mode (requires pytest-watch)
# uv add --dev pytest-watch
# ptw

# Or run tests manually after changes
pytest

# Run with coverage
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Frontend Development

#### For component/hook development:

```bash
cd apps/frontend

# Run Vitest in watch mode
npm run test:watch

# Or use UI mode
npm run test:ui
```

#### For E2E test development:

```bash
cd apps/frontend

# Generate test code by recording actions
npm run test:e2e:codegen

# Run E2E tests in UI mode
npm run test:e2e:ui
```

## 🔧 Configuration Files

All configurations are ready to use:

- ✅ `apps/backend/pyproject.toml` - pytest configuration
- ✅ `apps/frontend/vitest.config.ts` - Vitest configuration
- ✅ `apps/frontend/playwright.config.ts` - Playwright configuration
- ✅ `apps/frontend/src/setupTests.ts` - Global test setup

## 📖 Documentation

Detailed documentation is available:

1. **[TESTING.md](TESTING.md)** - Quick reference guide
2. **[apps/backend/tests/README.md](apps/backend/tests/README.md)** - Backend testing guide
3. **[apps/frontend/tests/README.md](apps/frontend/tests/README.md)** - Frontend testing guide

## 🐛 Troubleshooting

### Backend: "ModuleNotFoundError"

```bash
# Make sure you're in the right directory
cd apps/backend

# Make sure dependencies are installed
uv sync --group test
```

### Frontend: "Cannot find module"

```bash
# Reinstall dependencies
cd apps/frontend
rm -rf node_modules package-lock.json
npm install
```

### Playwright: "Executable doesn't exist"

```bash
# Install Playwright browsers
npx playwright install chromium
```

### Port 5173 Already in Use

```bash
# Kill the process using the port
lsof -ti:5173 | xargs kill -9

# Or change the port in playwright.config.ts
```

## 🎓 Learning Resources

### Backend Testing

- [pytest documentation](https://docs.pytest.org/)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- Example tests in `apps/backend/tests/unit/test_example_service.py`

### Frontend Unit Testing

- [Vitest documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- Example tests in `apps/frontend/src/__tests__/`

### Frontend E2E Testing

- [Playwright documentation](https://playwright.dev/)
- [Page Object Model pattern](https://playwright.dev/docs/pom)
- Example tests in `apps/frontend/e2e/`

## 📊 CI/CD Ready

Your testing setup is CI/CD ready! The following commands can be used in your pipeline:

```yaml
# Backend
- cd apps/backend && uv sync --group test
- cd apps/backend && pytest --cov=app --cov-report=xml

# Frontend
- cd apps/frontend && npm ci
- cd apps/frontend && npm test -- --coverage
- cd apps/frontend && npx playwright install chromium
- cd apps/frontend && npm run test:e2e
```

## ✨ Summary

You now have:

- ✅ Complete backend testing setup with pytest
- ✅ Complete frontend unit testing with Vitest
- ✅ Complete frontend E2E testing with Playwright
- ✅ Example tests demonstrating patterns
- ✅ Page Object Models for maintainable E2E tests
- ✅ Comprehensive documentation
- ✅ CI/CD-ready configuration

Happy Testing! 🚀
