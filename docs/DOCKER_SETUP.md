# Docker Setup Guide - SchizoDot AI

## Overview

The SchizoDot AI system runs as **6 Docker containers** orchestrated via Docker Compose:

1. **fastapi-backend** - Main API server (FastAPI)
2. **redis** - Message queue for background tasks
3. **celery-worker** - Background job processor
4. **ai-pipeline** - AI models (emotion detection, object detection)
5. **nginx** - Reverse proxy (production entry point)
6. **flower** - Celery monitoring dashboard (optional)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         NGINX (Port 80)                      │
│                    Reverse Proxy Layer                       │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌──────────────────┐            ┌──────────────────┐
│  FastAPI Backend │            │   AI Pipeline    │
│    (Port 8000)   │◄──────────►│   (Port 8001)    │
└────────┬─────────┘            └──────────────────┘
         │                               │
         │                               │
         ▼                               ▼
┌──────────────────┐            ┌──────────────────┐
│      Redis       │◄───────────│  Celery Worker   │
│   (Port 6379)    │            │  (Background)    │
└──────────────────┘            └──────────────────┘
         │
         ▼
┌──────────────────┐
│     Flower       │
│   (Port 5555)    │
│   Monitoring     │
└──────────────────┘
```

## Prerequisites

### Required Software
- **Docker**: Version 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose**: Version 2.0+ (included with Docker Desktop)
- **Git**: For repository management

### System Requirements
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 20GB free space (for models and uploads)
- **OS**: macOS, Linux, or Windows with WSL2

### AWS Prerequisites
- AWS account with IAM user configured
- S3 bucket: `schizodot-backend-storage`
- DynamoDB tables: `SchizodotUsers`, `SchizodotJobs`
- AWS credentials (Access Key ID and Secret Access Key)

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/your-org/schizodot-ai-dot.git
cd schizodot-ai-dot
```

### 2. Configure Environment Variables
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your actual values
nano .env  # or use your preferred editor
```

**Required variables to set:**
```bash
AWS_ACCESS_KEY_ID=your_actual_key
AWS_SECRET_ACCESS_KEY=your_actual_secret
S3_BUCKET=schizodot-backend-storage
DYNAMO_TABLE=SchizodotUsers
DYNAMO_TABLE_JOBS=SchizodotJobs
```

### 3. Build Docker Images
```bash
# Build all containers
docker-compose build

# Or build specific service
docker-compose build fastapi-backend
```

### 4. Start All Services
```bash
# Start in detached mode (background)
docker-compose up -d

# Or start with logs visible
docker-compose up
```

### 5. Verify Services
```bash
# Check all containers are running
docker-compose ps

# Expected output:
# NAME                    STATUS              PORTS
# schizodot-fastapi       Up (healthy)        0.0.0.0:8000->8000/tcp
# schizodot-redis         Up (healthy)        0.0.0.0:6379->6379/tcp
# schizodot-worker        Up                  
# schizodot-ai-pipeline   Up (healthy)        0.0.0.0:8001->8001/tcp
# schizodot-nginx         Up (healthy)        0.0.0.0:80->80/tcp
# schizodot-flower        Up                  0.0.0.0:5555->5555/tcp
```

### 6. Test Endpoints
```bash
# Test health endpoint via Nginx
curl http://localhost/api/v1/health

# Expected: {"status":"ok"}

# Test FastAPI directly
curl http://localhost:8000/api/v1/health

# Access API documentation
open http://localhost:8000/docs

# Access Flower monitoring
open http://localhost:5555
```

## Container Details

### 1. FastAPI Backend (Port 8000)

**Purpose**: Main API server handling all HTTP requests

**Key Features**:
- S3 presigned URL generation
- DynamoDB logging
- Job queue management
- CORS configuration

**Environment Variables**:
- `AWS_*` - AWS credentials and configuration
- `REDIS_HOST` - Redis connection
- `AI_PIPELINE_URL` - Internal AI service URL

**Health Check**: `GET /api/v1/health`

**Logs**:
```bash
docker-compose logs -f fastapi-backend
```

---

### 2. Redis (Port 6379)

**Purpose**: Message broker for Celery task queue

**Key Features**:
- Task queue storage
- Result backend
- Pub/sub messaging

**Data Persistence**: Volume `redis_data`

**Health Check**: `redis-cli ping`

**Logs**:
```bash
docker-compose logs -f redis
```

---

### 3. Celery Worker

**Purpose**: Background task processor for AI analysis

**Key Features**:
- Asynchronous job processing
- S3 file downloads
- AI model orchestration
- Result storage to DynamoDB

**Concurrency**: 2 workers (configurable)

**Tasks**:
- `analyze_media` - Main analysis pipeline
- `process_emotion` - Emotion detection
- `process_object_detection` - Pill verification
- `bedrock_fusion` - LLM analysis

**Logs**:
```bash
docker-compose logs -f celery-worker
```

---

### 4. AI Pipeline (Port 8001)

**Purpose**: AI model inference service

**Key Features**:
- Emotion detection (audio + face)
- Object detection (pill verification)
- Model caching
- GPU support (optional)

**Models**:
- Audio emotion: Librosa + CNN
- Face emotion: PyTorch CNN
- Object detection: YOLOv8 (future)

**Health Check**: `GET /health`

**Logs**:
```bash
docker-compose logs -f ai-pipeline
```

---

### 5. Nginx (Port 80)

**Purpose**: Reverse proxy and load balancer

**Key Features**:
- Route `/api/*` to FastAPI
- SSL/TLS termination (production)
- Request logging
- Static file serving (future)

**Configuration**: `infra/nginx/nginx.conf`

**Logs**:
```bash
docker-compose logs -f nginx
# Or view nginx access logs
tail -f logs/nginx/access.log
```

---

### 6. Flower (Port 5555)

**Purpose**: Celery monitoring dashboard

**Key Features**:
- Real-time task monitoring
- Worker status
- Task history
- Performance metrics

**Access**: http://localhost:5555

**Logs**:
```bash
docker-compose logs -f flower
```

## Common Commands

### Start/Stop Services
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart fastapi-backend

# Stop and remove volumes (CAUTION: deletes data)
docker-compose down -v
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f fastapi-backend

# Last 100 lines
docker-compose logs --tail=100 celery-worker
```

### Execute Commands in Container
```bash
# Open shell in FastAPI container
docker-compose exec fastapi-backend /bin/bash

# Run Python script
docker-compose exec fastapi-backend python -c "print('Hello')"

# Check Celery worker status
docker-compose exec celery-worker celery -A app.worker inspect active
```

### Rebuild After Code Changes
```bash
# Rebuild and restart
docker-compose up -d --build

# Rebuild specific service
docker-compose build fastapi-backend
docker-compose up -d fastapi-backend
```

### View Resource Usage
```bash
# Container stats
docker stats

# Disk usage
docker system df
```

## Troubleshooting

### Container Won't Start

**Check logs**:
```bash
docker-compose logs fastapi-backend
```

**Common issues**:
- Missing environment variables → Check `.env` file
- Port already in use → Change port in `docker-compose.yml`
- AWS credentials invalid → Verify in AWS Console

---

### Redis Connection Failed

**Symptoms**: Worker can't connect to Redis

**Solution**:
```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping
# Should return: PONG

# Restart Redis
docker-compose restart redis
```

---

### AI Pipeline Out of Memory

**Symptoms**: Container crashes with OOM error

**Solution**:
```yaml
# Edit docker-compose.yml
ai-pipeline:
  deploy:
    resources:
      limits:
        memory: 4G  # Increase memory limit
```

---

### Slow Model Loading

**Symptoms**: AI container takes 5+ minutes to start

**Solution**:
- Pre-download models during build
- Use model caching volume
- Consider using smaller models for development

---

### Permission Denied Errors

**Symptoms**: Can't write to volumes

**Solution**:
```bash
# Fix permissions
sudo chown -R $USER:$USER uploads/ logs/

# Or run with user ID
docker-compose run --user $(id -u):$(id -g) fastapi-backend
```

## Development vs Production

### Development Mode
```bash
# Use docker-compose.yml (default)
docker-compose up

# Features:
# - Hot reload enabled
# - Debug logging
# - Exposed ports for direct access
# - Flower monitoring enabled
```

### Production Mode
```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Features:
# - Optimized images
# - No hot reload
# - SSL/TLS enabled
# - Resource limits set
# - Health checks enabled
```

## Network Configuration

All containers run on the `schizodot-network` bridge network.

**Internal DNS**:
- `redis` → Redis service
- `fastapi-backend` → FastAPI service
- `ai-pipeline` → AI service

**External Access**:
- Port 80 → Nginx (production entry)
- Port 8000 → FastAPI (development)
- Port 5555 → Flower (monitoring)

## Volume Management

### Persistent Volumes
- `redis_data` - Redis database
- `./uploads` - Uploaded media files
- `./logs` - Application logs
- `./ai_models` - Cached AI models

### Backup Volumes
```bash
# Backup uploads
tar -czf uploads-backup.tar.gz uploads/

# Backup logs
tar -czf logs-backup.tar.gz logs/

# Backup Redis data
docker-compose exec redis redis-cli SAVE
docker cp schizodot-redis:/data/dump.rdb ./redis-backup.rdb
```

## Next Steps

After Docker setup is complete:
1. ✅ Verify all containers are healthy
2. ⏭️ Proceed to **Step 1.2**: Build FastAPI Dockerfile
3. ⏭️ Configure Nginx reverse proxy
4. ⏭️ Test end-to-end upload flow

## Support

For issues:
1. Check logs: `docker-compose logs -f`
2. Verify environment variables: `docker-compose config`
3. Review health checks: `docker-compose ps`
4. Consult main README.md
