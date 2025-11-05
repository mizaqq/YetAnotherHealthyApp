# Backend Tests

This directory contains the test suite for the YetAnotherHealthyApp backend API built with FastAPI.

## Test Structure

```
tests/
├── conftest.py           # Shared fixtures and test configuration
├── unit/                 # Unit tests for services and utilities
│   └── test_example_service.py
└── integration/          # Integration tests for API endpoints
    └── test_example_api.py
```

## Running Tests

### Install Dependencies

First, make sure you have the test dependencies installed:

```bash
cd apps/backend
uv sync --group test
```

### Run All Tests

```bash
# From apps/backend directory
pytest
```

### Run Specific Test Types

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run tests in a specific file
pytest tests/unit/test_example_service.py

# Run a specific test function
pytest tests/unit/test_example_service.py::test_addition
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View coverage report (opens in browser)
open htmlcov/index.html
```

### Watch Mode

For continuous testing during development:

```bash
# Install pytest-watch (optional)
uv add --dev pytest-watch

# Run in watch mode
ptw
```

## Writing Tests

### Unit Tests

Unit tests focus on testing individual functions and services in isolation. Use fixtures and mocks to isolate the code under test.

Example:

```python
import pytest

def test_calculate_macros():
    result = calculate_macros(calories=2000, protein_percent=30)
    assert result["protein"] == 150
```

### Integration Tests

Integration tests verify that API endpoints work correctly. Use the `test_client` or `async_client` fixtures from `conftest.py`.

Example:

```python
def test_health_endpoint(test_client):
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200
```

### Parameterized Tests

Use `@pytest.mark.parametrize` to test multiple inputs efficiently:

```python
@pytest.mark.parametrize(
    ("input_value", "expected"),
    [(0, 0), (1, 1), (2, 4), (3, 9)],
)
def test_square(input_value, expected):
    assert input_value ** 2 == expected
```

### Async Tests

For async functions, use `@pytest.mark.asyncio`:

```python
@pytest.mark.asyncio
async def test_async_endpoint(async_client):
    response = await async_client.get("/api/v1/meals")
    assert response.status_code == 200
```

### Mocking External Services

Use `monkeypatch` for simple mocking or `respx` for HTTP mocking:

```python
def test_with_mock(monkeypatch):
    def mock_function():
        return "mocked"

    monkeypatch.setattr("module.function", mock_function)
    # Test code here
```

## Available Fixtures

### From conftest.py

- `test_client`: Synchronous FastAPI TestClient
- `async_client`: Async HTTP client for async tests
- `mock_supabase_client`: Mocked Supabase client

### Built-in pytest fixtures

- `monkeypatch`: For mocking and patching
- `tmp_path`: Temporary directory for file operations
- `caplog`: Capture log messages
- `capsys`: Capture stdout/stderr

## Best Practices

1. **Test Organization**: Group related tests using `describe` pattern or test classes
2. **Fixtures**: Use fixtures for common setup to keep tests DRY
3. **Assertions**: Use descriptive assertions and error messages
4. **Isolation**: Each test should be independent and not rely on others
5. **Naming**: Use descriptive test names that explain what is being tested
6. **Coverage**: Aim for meaningful coverage, not just high percentages
7. **Fast Tests**: Keep unit tests fast; use integration tests for slower operations
8. **Markers**: Use markers (`@pytest.mark.unit`, `@pytest.mark.slow`) to categorize tests

## Configuration

Test configuration is in `pyproject.toml` under `[tool.pytest.ini_options]`:

- **testpaths**: `tests/` directory
- **coverage**: Configured to report on `app/` package
- **asyncio_mode**: Set to `auto` for automatic async handling
- **markers**: `unit`, `integration`, `slow`

## Debugging Tests

### Run with verbose output

```bash
pytest -v
```

### Show print statements

```bash
pytest -s
```

### Drop into debugger on failure

```bash
pytest --pdb
```

### Run last failed tests

```bash
pytest --lf
```

## CI/CD Integration

Tests run automatically in CI/CD pipeline. Ensure:

1. All tests pass before merging
2. Code coverage meets thresholds
3. No linting errors (run `ruff check .`)

## Common Issues

### Import Errors

Make sure you're running tests from the `apps/backend` directory or that your PYTHONPATH is set correctly.

### Async Test Issues

Ensure you have `pytest-asyncio` installed and use `@pytest.mark.asyncio` decorator.

### Database Tests

Use mocked clients for unit tests. For integration tests requiring a database, consider using test fixtures that set up/tear down test data.

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [FastAPI testing guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [respx documentation](https://lundberg.github.io/respx/)
