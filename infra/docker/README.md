# Docker Configuration - SchizoDot AI

## Overview

This directory contains all Dockerfiles for the SchizoDot AI system.

## Dockerfiles

### 1. Dockerfile.fastapi (Production)

**Purpose**: Production-ready FastAPI backend with optimized multi-stage build

**Features**:
- Multi-stage build (reduces final image size by ~60%)
- Non-root user for security
- Gunicorn with Uvicorn workers for production performance
- Health checks configured
- Optimized layer caching

**Build**:
```bash
docker build -f infra/docker/Dockerfile.fastapi -t schizodot-fastapi .
```

**Run standalone**:
```bash
docker run -p 8000:8000 \
  -e AWS_REGION=us-east-1 \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  schizodot-fastapi
```

**Image size**: ~200-300MB (vs ~800MB without multi-stage)

---

### 2. Dockerfile.fastapi.dev (Development)

**Purpose**: Development version with hot-reload support

**Features**:
- Single-stage build (faster rebuilds)
- Hot-reload enabled (code changes reflect immediately)
- Debug logging
- Volume mounts for live code editing

**Build**:
```bash
docker build -f infra/docker/Dockerfile.fastapi.dev -t schizodot-fastapi-dev .
```

**Run with volume mount**:
```bash
docker run -p 8000:8000 \
  -v $(pwd)/backend/app:/app \
  -e AWS_REGION=us-east-1 \
  schizodot-fastapi-dev
```

**When to use**:
- Local development
- Testing code changes quickly
- Debugging issues

---

### 3. Dockerfile.worker (Production)

**Purpose**: Celery worker for background task processing

**Features**:
- Multi-stage build for optimization
- Celery with Redis backend
- Concurrent task processing (2 workers default)
- AWS SDK for S3/DynamoDB access
- AI service integration via HTTP
- Task retry logic and timeouts
- Health checks via Celery inspect

**Build**:
```bash
docker-compose build celery-worker
```

**Run standalone**:
```bash
docker run \
  -e REDIS_HOST=redis \
  -e AWS_REGION=us-east-1 \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  schizodot-worker
```

**Tasks handled**:
- `analyze_media` - Main orchestration task
- S3 file downloads
- AI service coordination
- Result storage to DynamoDB

**Status**: ✅ Complete (Step 1.3)

---

### 4. Dockerfile.ai-pipeline (Production)

**Purpose**: AI model inference service

**Features**:
- PyTorch runtime (CPU version, GPU optional)
- Pre-loaded emotion detection models
- FastAPI service on port 8001
- FFmpeg for video processing
- Model caching in /models volume
- Lazy model loading for faster startup

**Build**:
```bash
docker-compose build ai-pipeline
```

**Run standalone**:
```bash
docker run -p 8001:8001 \
  -v $(pwd)/ai_models:/models \
  schizodot-ai-pipeline
```

**Endpoints**:
- `GET /health` - Health check
- `POST /emotion/analyze` - Emotion detection (audio + face)
- `POST /object-detection/analyze` - Pill verification (mock)

**Image size**: ~1.5-2GB (includes PyTorch, OpenCV, audio libs)

**Status**: ✅ Complete (Step 1.4)

---

## Build Optimization

### Multi-Stage Build Benefits

**Stage 1 (Builder)**:
- Installs build tools (gcc, g++, make)
- Compiles Python packages
- Creates wheel files
- ~800MB size

**Stage 2 (Runtime)**:
- Copies only compiled packages
- Minimal runtime dependencies
- No build tools
- ~250MB size

**Result**: 60-70% size reduction

### Layer Caching Strategy

Layers ordered by change frequency:
1. System packages (rarely change)
2. Python dependencies (change occasionally)
3. Application code (change frequently)

This ensures fast rebuilds when only code changes.

---

## Security Best Practices

### 1. Non-Root User
```dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```
- Prevents privilege escalation
- Limits container access
- Industry best practice

### 2. No Secrets in Image
- Environment variables at runtime only
- No hardcoded credentials
- Use Docker secrets or .env files

### 3. Minimal Base Image
- `python:3.10-slim` instead of full Python
- Reduces attack surface
- Faster pulls and starts

### 4. Security Scanning
```bash
# Scan for vulnerabilities
docker scan schizodot-fastapi
```

---

## Health Checks

All production images include health checks:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1
```

**Benefits**:
- Docker knows when container is ready
- Auto-restart on failure
- Load balancer integration
- Monitoring integration

**Check status**:
```bash
docker ps
# Look for "healthy" status
```

---

## Environment Variables

### Required Variables

**AWS Configuration**:
```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET=schizodot-backend-storage
DYNAMO_TABLE=SchizodotUsers
```

**Redis/Celery**:
```bash
REDIS_HOST=redis
REDIS_PORT=6379
CELERY_BROKER_URL=redis://redis:6379/0
```

**API Configuration**:
```bash
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000
```

### Optional Variables

```bash
ENV=production
LOG_LEVEL=INFO
BEDROCK_ENABLE=true
BEDROCK_MODEL_ID=anthropic.claude-v2
```

---

## Testing Docker Builds

### Quick Test
```bash
# Build and test FastAPI image
./scripts/test-docker-build.sh
```

### Manual Testing

**1. Build image**:
```bash
docker-compose build fastapi-backend
```

**2. Check image exists**:
```bash
docker images | grep schizodot
```

**3. Test container starts**:
```bash
docker-compose up fastapi-backend
```

**4. Test health endpoint**:
```bash
curl http://localhost:8000/api/v1/health
```

**5. Check logs**:
```bash
docker-compose logs fastapi-backend
```

---

## Troubleshooting

### Build Fails with "requirements.txt not found"

**Cause**: Running from wrong directory

**Solution**:
```bash
# Must run from project root
cd /path/to/schizodot-ai-dot
docker-compose build
```

---

### Build is Very Slow

**Cause**: Not using layer caching

**Solution**:
```bash
# Use BuildKit for better caching
export DOCKER_BUILDKIT=1
docker-compose build
```

---

### Container Exits Immediately

**Cause**: Missing environment variables

**Solution**:
```bash
# Check logs
docker-compose logs fastapi-backend

# Verify .env file exists
cat .env

# Test with minimal config
docker-compose run fastapi-backend env
```

---

### "Permission Denied" Errors

**Cause**: Volume mount permission issues

**Solution**:
```bash
# Fix ownership
sudo chown -R $USER:$USER backend/app

# Or run as current user
docker-compose run --user $(id -u):$(id -g) fastapi-backend
```

---

### Image Size Too Large

**Cause**: Not using multi-stage build

**Solution**:
```bash
# Use production Dockerfile
docker build -f infra/docker/Dockerfile.fastapi .

# Check size
docker images schizodot-fastapi
```

---

## Performance Tuning

### Gunicorn Workers

**Formula**: `(2 x CPU cores) + 1`

For 4-core machine:
```dockerfile
CMD ["gunicorn", "app.main:app", \
     "--workers", "9", \
     "--worker-class", "uvicorn.workers.UvicornWorker"]
```

### Memory Limits

Set in docker-compose.yml:
```yaml
fastapi-backend:
  deploy:
    resources:
      limits:
        memory: 2G
      reservations:
        memory: 1G
```

### CPU Limits

```yaml
fastapi-backend:
  deploy:
    resources:
      limits:
        cpus: '2.0'
      reservations:
        cpus: '1.0'
```

---

## Development Workflow

### 1. Code Changes
```bash
# Edit code in backend/app/
vim backend/app/main.py

# Changes auto-reload (dev mode)
# Or rebuild (production mode)
docker-compose up -d --build fastapi-backend
```

### 2. Add Dependencies
```bash
# Add to requirements.txt
echo "new-package==1.0.0" >> backend/app/requirements.txt

# Rebuild image
docker-compose build fastapi-backend

# Restart container
docker-compose up -d fastapi-backend
```

### 3. Debug Issues
```bash
# Enter container shell
docker-compose exec fastapi-backend /bin/bash

# Check Python environment
python -c "import sys; print(sys.path)"

# Test imports
python -c "from app.main import app; print(app)"
```

---

## Next Steps

After FastAPI Dockerfile is complete:
1. ✅ Test build with `./scripts/test-docker-build.sh`
2. ⏭️ Create Dockerfile.worker (Celery)
3. ⏭️ Create Dockerfile.ai-pipeline (AI models)
4. ⏭️ Configure Nginx
5. ⏭️ Test full stack with `docker-compose up`

---

## References

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [FastAPI in Containers](https://fastapi.tiangolo.com/deployment/docker/)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/stable/configure.html)
