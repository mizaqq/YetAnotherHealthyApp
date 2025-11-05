# Docker Deployment Guide

This guide explains how to build and run the YetAnotherHealthyApp backend using Docker.

## Quick Start

### Prerequisites

- Docker 20.10+ with BuildKit support
- Git (for version tagging)
- Your API credentials (Supabase, OpenRouter)

### Build the Image

```bash
cd apps/backend
chmod +x docker-build.sh docker-run.sh
./docker-build.sh
```

This creates two tags:
- `yetanotherhealthyapp-backend:latest`
- `yetanotherhealthyapp-backend:<git-commit-sha>`

### Run the Container

**Option 1: Using environment file (recommended)**

Create `.env.production` with your credentials:

```bash
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_actual_service_role_key
OPENROUTER_API_KEY=your_actual_openrouter_api_key

CORS_ORIGINS=["https://your-frontend-domain.com","https://www.your-frontend-domain.com"]
```

Then run:

```bash
./docker-run.sh
```

**Option 2: Manual docker run with environment variables**

```bash
docker run -d \
  --name yetanotherhealthyapp-backend \
  -e APP_ENV=production \
  -e SUPABASE_URL=https://your-project.supabase.co \
  -e SUPABASE_SERVICE_ROLE_KEY=your_service_role_key \
  -e OPENROUTER_API_KEY=your_openrouter_key \
  -e CORS_ORIGINS='["https://your-domain.com"]' \
  -p 8000:8000 \
  --memory="512m" \
  --cpus="1.0" \
  --restart=unless-stopped \
  yetanotherhealthyapp-backend:latest
```

### Verify Deployment

Check health endpoint:

```bash
curl http://localhost:8000/api/v1/health
# Expected: {"status":"ok"}
```

View logs:

```bash
docker logs -f yetanotherhealthyapp-backend
```

## Detailed Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | `https://abc123.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (keep secret!) | `eyJhbGciOiJIUzI1NiIs...` |
| `OPENROUTER_API_KEY` | OpenRouter API key | `sk-or-v1-...` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment name | `production` |
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `CORS_ORIGINS` | Allowed CORS origins (JSON array) | `["http://localhost:5173"]` |
| `OPENROUTER_DEFAULT_MODEL` | AI model for analysis | `google/gemini-2.0-flash-001` |
| `OPENROUTER_DEFAULT_TEMPERATURE` | Model temperature | `0.2` |
| `OPENROUTER_MAX_OUTPUT_TOKENS` | Max output tokens | `600` |

See `README_ENV.md` for complete list of configuration options.

## Image Architecture

### Multi-Stage Build

**Stage 1: Builder**
- Base: `python:3.13-slim`
- Installs dependencies using `uv` package manager
- Copies application code

**Stage 2: Runtime**
- Base: `python:3.13-slim`
- Copies only compiled dependencies and app code
- Runs as non-root user `appuser` (UID 1000)
- Includes health check monitoring

### Security Features

- **Non-root execution**: Runs as `appuser` (UID 1000)
- **Minimal image**: Only runtime dependencies included
- **No secrets in image**: All credentials loaded at runtime
- **Read-only recommended**: Can run with `--read-only` flag (use tmpfs for /tmp)

### Resource Limits

Recommended limits:
- **Memory**: 512MB minimum, 1GB recommended for production
- **CPU**: 1.0 CPU minimum, 2.0 recommended for production
- **Storage**: ~300MB image size

## Advanced Usage

### Custom Image Name and Tag

```bash
./docker-build.sh my-backend-image v1.2.3
```

This creates:
- `my-backend-image:v1.2.3`
- `my-backend-image:<git-commit-sha>`

### Running with Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    image: yetanotherhealthyapp-backend:latest
    container_name: yetanotherhealthyapp-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      APP_ENV: production
      DEBUG: "false"
      LOG_LEVEL: INFO
      SUPABASE_URL: ${SUPABASE_URL}
      SUPABASE_SERVICE_ROLE_KEY: ${SUPABASE_SERVICE_ROLE_KEY}
      OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}
      CORS_ORIGINS: '["https://your-domain.com"]'
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

Run with:

```bash
docker-compose up -d
```

### Read-Only Filesystem (Enhanced Security)

```bash
docker run -d \
  --name yetanotherhealthyapp-backend \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=100m \
  -e APP_ENV=production \
  -e SUPABASE_URL=your_url \
  -e SUPABASE_SERVICE_ROLE_KEY=your_key \
  -e OPENROUTER_API_KEY=your_key \
  -p 8000:8000 \
  yetanotherhealthyapp-backend:latest
```

### Development Mode (Not Recommended for Production)

For local testing with hot reload:

```bash
docker run -it --rm \
  -v $(pwd)/app:/app/app:ro \
  -e APP_ENV=development \
  -e DEBUG=true \
  -e LOG_LEVEL=DEBUG \
  -p 8000:8000 \
  yetanotherhealthyapp-backend:latest \
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Container Management

### View Logs

```bash
# Follow logs in real-time
docker logs -f yetanotherhealthyapp-backend

# Last 100 lines
docker logs --tail 100 yetanotherhealthyapp-backend

# With timestamps
docker logs -t yetanotherhealthyapp-backend
```

### Inspect Container

```bash
# Container details
docker inspect yetanotherhealthyapp-backend

# Resource usage
docker stats yetanotherhealthyapp-backend

# Health status
docker inspect --format='{{.State.Health.Status}}' yetanotherhealthyapp-backend
```

### Stop and Remove

```bash
# Stop container
docker stop yetanotherhealthyapp-backend

# Remove container
docker rm yetanotherhealthyapp-backend

# Stop and remove in one command
docker rm -f yetanotherhealthyapp-backend
```

### Update Container

```bash
# Pull/build new image
./docker-build.sh

# Stop old container
docker stop yetanotherhealthyapp-backend
docker rm yetanotherhealthyapp-backend

# Start new container
./docker-run.sh
```

## Production Deployment

### DigitalOcean App Platform

1. **Push image to registry:**

```bash
# Tag for DigitalOcean Container Registry
docker tag yetanotherhealthyapp-backend:latest \
  registry.digitalocean.com/your-registry/backend:latest

# Push to registry
docker push registry.digitalocean.com/your-registry/backend:latest
```

2. **Create App Platform app:**
   - Select "Docker Hub or Container Registry"
   - Configure environment variables in App Platform UI
   - Set health check endpoint: `/api/v1/health`
   - Configure resource size (minimum: Basic plan)

3. **Set environment variables in App Platform:**
   - Add all required variables as encrypted environment variables
   - Use App Platform's secret management for sensitive data

### Docker Swarm / Kubernetes

For orchestrated deployments, use the provided `docker-compose.yml` as a starting point and adapt to your orchestration platform's configuration format.

**Kubernetes example snippet:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: backend
        image: yetanotherhealthyapp-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: APP_ENV
          value: "production"
        - name: SUPABASE_URL
          valueFrom:
            secretKeyRef:
              name: backend-secrets
              key: supabase-url
        # ... more env vars
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 40
          periodSeconds: 30
```

## Troubleshooting

### Container Won't Start

**Check logs:**
```bash
docker logs yetanotherhealthyapp-backend
```

**Common issues:**
- Missing required environment variables (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, OPENROUTER_API_KEY)
- Invalid environment variable format (especially CORS_ORIGINS JSON array)
- Port 8000 already in use

**Solutions:**
```bash
# Verify environment variables are set
docker inspect yetanotherhealthyapp-backend | grep -A 20 Env

# Check if port is in use
lsof -i :8000

# Run interactively to debug
docker run -it --rm \
  -e APP_ENV=production \
  -e SUPABASE_URL=your_url \
  -e SUPABASE_SERVICE_ROLE_KEY=your_key \
  -e OPENROUTER_API_KEY=your_key \
  yetanotherhealthyapp-backend:latest \
  /bin/bash
```

### Health Check Failing

**Symptoms:**
- Container status shows "unhealthy"
- Application not responding

**Diagnosis:**
```bash
# Check if process is running
docker exec yetanotherhealthyapp-backend ps aux

# Test health endpoint from inside container
docker exec yetanotherhealthyapp-backend curl http://localhost:8000/api/v1/health

# Check uvicorn logs
docker logs yetanotherhealthyapp-backend | grep uvicorn
```

**Solutions:**
- Increase `start-period` in HEALTHCHECK if startup is slow
- Verify application is binding to 0.0.0.0 not 127.0.0.1
- Check for errors in application logs

### Build Failures

**uv sync fails:**
```bash
# Clear build cache and rebuild
docker builder prune
./docker-build.sh
```

**Dependency conflicts:**
- Ensure `uv.lock` is up to date
- Run `uv lock` locally first
- Check Python version matches (3.13)

### Performance Issues

**High memory usage:**
```bash
# Check memory stats
docker stats yetanotherhealthyapp-backend

# Increase memory limit
docker update --memory="1g" yetanotherhealthyapp-backend
```

**Slow requests:**
- Check OpenRouter API response times
- Enable DEBUG logging temporarily
- Monitor Supabase connection pool

### Permission Issues

**File permission errors:**
- Verify all files are accessible to UID 1000 (appuser)
- Check volume mount permissions if using volumes

## Best Practices

### Security

1. **Never commit secrets**: Use environment variables or secret management
2. **Scan images regularly**: `docker scan yetanotherhealthyapp-backend:latest`
3. **Keep base image updated**: Rebuild regularly for security patches
4. **Use specific tags**: Avoid `:latest` in production, use commit SHAs
5. **Limit container privileges**: Don't use `--privileged` flag

### Performance

1. **Use health checks**: Monitor container health automatically
2. **Set resource limits**: Prevent resource exhaustion
3. **Enable logging**: Configure log rotation to prevent disk fill
4. **Monitor metrics**: Use Prometheus or similar for production monitoring

### Maintenance

1. **Regular updates**: Rebuild images monthly for security updates
2. **Backup environment config**: Store `.env` files securely
3. **Document changes**: Update this README when changing configuration
4. **Test before deploying**: Always test new images in staging first

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [uv Package Manager](https://github.com/astral-sh/uv)
- Backend Environment Configuration: `README_ENV.md`

## Support

For issues or questions:
1. Check application logs: `docker logs yetanotherhealthyapp-backend`
2. Review this documentation
3. Check `README_ENV.md` for environment configuration
4. Verify all required environment variables are set correctly

