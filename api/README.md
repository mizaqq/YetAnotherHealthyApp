# Calorie Intake Logger API

FastAPI backend for the Calorie Intake Logger PoC.

## Quick Start

1. **Install uv (if not already installed):**

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # or: brew install uv
   ```

2. **Install dependencies:**

   ```bash
   make install
   # or: cd api && uv sync
   ```

3. **Configure environment:**

   ```bash
   cp api/.env.example api/.env
   # Edit .env with your configuration
   ```

4. **Run development server:**

   ```bash
   make dev
   ```

5. **Access API documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - OpenAPI JSON: http://localhost:8000/api/v1/openapi.json

## Development

### Available Commands

- `make sync` - Sync dependencies using uv
- `make install` - Install dependencies (alias for sync)
- `make dev` - Run development server with hot reload
- `make openapi` - Export OpenAPI schema to `docs/openapi.json`
- `make test` - Run tests
- `make lint` - Run linter
- `make format` - Format code
- `make ci` - Run CI checks (lint + test)

All commands use `uv` for fast, reliable Python package management.

### Project Structure

```
api/
├── app/
│   ├── main.py              # FastAPI application
│   ├── api/
│   │   └── routers/         # API endpoints
│   ├── models/              # Pydantic models
│   ├── services/            # Business logic
│   ├── repositories/        # Data access
│   ├── clients/             # External clients
│   ├── core/                # Core utilities
│   │   ├── settings.py      # Configuration
│   │   ├── exceptions.py    # Error handling
│   │   └── logging.py       # Logging setup
│   └── scripts/             # Utility scripts
├── tests/                   # Test suite
├── pyproject.toml          # Project config
└── requirements.txt        # Dependencies
```

## API Endpoints

### Parse

- `POST /api/v1/parse` - Parse natural language food description

### Match

- `POST /api/v1/match` - Match food items to database

### Log

- `POST /api/v1/log` - Log a meal (requires auth)

### Summary

- `GET /api/v1/summary?date=YYYY-MM-DD` - Get daily summary (requires auth)

### Foods

- `GET /api/v1/foods/search?q=<query>` - Search foods

## Configuration

All configuration is managed via environment variables with the `BACKEND_` prefix. See `.env.example` for all available options.

## Testing

Run the test suite:

```bash
make test
```

With coverage:

```bash
cd api && pytest --cov=app --cov-report=html
```

## Linting and Formatting

```bash
make lint     # Check code
make format   # Format code
```
