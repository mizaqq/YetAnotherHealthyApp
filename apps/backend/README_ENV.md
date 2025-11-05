# Backend Environment Configuration

This document explains how to configure environment variables for different deployment environments.

## Environment File Hierarchy

The application loads environment files in the following priority order:

1. `.env` (base configuration - always loaded)
2. `.env.{environment}` (environment-specific)
3. `.env.{environment}.local` (environment-specific local overrides)
4. `.env.local` (local overrides - always loaded last)

## Supported Environments

- **development** (default)
- **staging**
- **production**
- **test**

## Environment Variables

Set `APP_ENV` to control which environment-specific files are loaded:

```bash
export APP_ENV=production
```

Or set it in your shell profile (`.bashrc`, `.zshrc`, etc.):

```bash
echo 'export APP_ENV=production' >> ~/.zshrc
```

### Required Environment Variables

| Variable                    | Description          | Example                            |
| --------------------------- | -------------------- | ---------------------------------- |
| `SUPABASE_URL`              | Supabase project URL | `https://your-project.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key     | `eyJhbGciOiJIUzI1NiIs...`          |
| `OPENROUTER_API_KEY`        | OpenRouter API key   | `sk-or-v1-...`                     |

### Optional Environment Variables

| Variable                         | Description          | Default              |
| -------------------------------- | -------------------- | -------------------- | --- |
| `APP_ENV`                        | Environment name     | development          |
| `DEBUG`                          | Enable debug mode    | false                |
| `LOG_LEVEL`                      | Logging level        | INFO                 |
| `CORS_ORIGINS`                   | Allowed CORS origins | localhost:5173       |
| `OPENROUTER_DEFAULT_MODEL`       | Default model        | gemini-2.0-flash-001 |
| `OPENROUTER_DEFAULT_TEMPERATURE` | Response temperature | 0.2                  |
| `OPENROUTER_MAX_OUTPUT_TOKENS`   | Max output tokens    | 600                  |     |

## Quick Setup

1. **Create base environment file:**

   ```bash
   cd apps/backend
   python scripts/create_env.py development
   ```

2. **Edit the created file** (`.env.development.example`):

   ```bash
   # Replace placeholder values with your actual API keys
   SUPABASE_URL=https://your-actual-project.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your_actual_service_role_key
   OPENROUTER_API_KEY=your_actual_openrouter_key
   ```

3. **Rename to activate:**

   ```bash
   mv .env.development.example .env.development
   ```

4. **Run the application:**
   ```bash
   uv run dev  # Development mode
   ```

## Usage Examples

### Development Setup

After creating your environment file:

```bash
# .env.development
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG

SUPABASE_URL=https://your-dev-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_dev_service_role_key

OPENROUTER_API_KEY=your_dev_openrouter_key

CORS_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173"]
```

### Production Setup

```bash
# Create production environment file
python scripts/create_env.py production

# Edit the created file with your production values
# Then rename: mv .env.production.example .env.production

# Or create manually:
# .env.production
APP_ENV=production
DEBUG=false
LOG_LEVEL=WARNING

SUPABASE_URL=https://your-prod-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_prod_service_role_key

OPENROUTER_API_KEY=your_prod_openrouter_key

CORS_ORIGINS=["https://your-domain.com", "https://www.your-domain.com"]
```

### Running with Specific Environment

```bash
# Development
APP_ENV=development python -m uvicorn app.main:app --reload

# Production
APP_ENV=production python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Staging
APP_ENV=staging python -m uvicorn app.main:app
```

## Environment-Specific Overrides

### Nested Configuration

Use double underscores for nested configuration:

```bash
# Instead of environment-specific files, you can use:
OPENROUTER__DEFAULT_MODEL=your_model
OPENROUTER__API_KEY=your_key
```

### Local Overrides

Create `.env.local` for machine-specific overrides that shouldn't be committed:

```bash
# .env.local
SUPABASE_URL=https://localhost:54321
OPENROUTER_API_KEY=sk-local-development-key
```

## Docker Deployment

For Docker deployments, set environment variables directly:

```bash
docker run -e APP_ENV=production \
  -e SUPABASE_URL=your_url \
  -e SUPABASE_SERVICE_ROLE_KEY=your_key \
  -e OPENROUTER_API_KEY=your_key \
  your-image
```

## Testing

For tests, use:

```bash
APP_ENV=test python -m pytest
```

This will load `.env.test` and `.env.test.local` files.

## Troubleshooting

### Common Issues

**"Missing required environment variables" error:**

- Ensure all required variables are set in your `.env` files
- Check that your `.env` file exists and is in the `apps/backend/` directory
- Verify variable names match exactly (case-sensitive)

**Environment files not loading:**

```bash
# Check which files are being loaded
python -c "
from app.core.config import settings
print('Environment files loaded:')
print('Current APP_ENV:', settings.app_env)
print('SUPABASE_URL:', settings.supabase_url)
print('DEBUG:', settings.debug)
"
```

**CORS issues:**

- Update `CORS_ORIGINS` in your environment file to include your frontend URL
- For JSON arrays, use proper format: `["https://example.com", "https://app.example.com"]`

**OpenRouter API errors:**

- Verify your `OPENROUTER_API_KEY` is valid
- Check your internet connection
- Ensure the API key has sufficient credits

### Environment File Priority

Files are loaded in this order (later files override earlier ones):

1. `.env` (base)
2. `.env.development` (if `APP_ENV=development`)
3. `.env.development.local` (if `APP_ENV=development`)
4. `.env.local` (always loaded last)

### Getting Help

- Check the application logs: `uv run dev` (includes detailed error messages)
- Validate your configuration: `uv run test-env` (shows current settings)
- Run comprehensive config test: `uv run test-config` (validates all settings)
- Review this README: `cat README_ENV.md`

**Quick Environment Check:**

```bash
# Test your current configuration
uv run test-config

# This will show you exactly what's loaded and highlight any missing variables
```
