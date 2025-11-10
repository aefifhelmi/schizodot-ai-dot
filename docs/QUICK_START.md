# Quick Start Guide - SchizoDot AI

## Prerequisites

- Docker Desktop installed and running
- AWS credentials configured
- 8GB+ RAM available
- 20GB+ disk space

## 1. Initial Setup (First Time Only)

```bash
# Clone repository
git clone https://github.com/your-org/schizodot-ai-dot.git
cd schizodot-ai-dot

# Copy environment template
cp .env.example .env

# Edit with your AWS credentials
nano .env
```

**Required variables in .env:**
```bash
AWS_ACCESS_KEY_ID=your_actual_key
AWS_SECRET_ACCESS_KEY=your_actual_secret
S3_BUCKET=schizodot-backend-storage
DYNAMO_TABLE=SchizodotUsers
DYNAMO_TABLE_JOBS=SchizodotJobs
```

## 2. Build and Start

```bash
# Build all images (10-15 minutes first time)
docker-compose build

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

## 3. Verify Services

```bash
# Run automated tests
./scripts/test-full-stack.sh

# Or manually check:
curl http://localhost/health              # Nginx
curl http://localhost/api/v1/health       # FastAPI
curl http://localhost:8001/health         # AI Pipeline
```

## 4. Access Services

| Service | URL | Purpose |
|---------|-----|---------|
| API | http://localhost/api/v1/ | Main API |
| Docs | http://localhost/docs | Swagger UI |
| Flower | http://localhost:5555 | Celery monitoring |
| Test Upload | frontend/index.html | Upload test page |

## 5. Common Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f fastapi-backend
docker-compose logs -f celery-worker
docker-compose logs -f ai-pipeline
```

### Restart Services
```bash
# All services
docker-compose restart

# Specific service
docker-compose restart fastapi-backend
```

### Stop Services
```bash
# Stop all
docker-compose down

# Stop and remove volumes (CAUTION: deletes data)
docker-compose down -v
```

### Rebuild After Code Changes
```bash
# Rebuild and restart
docker-compose up -d --build

# Specific service
docker-compose build fastapi-backend
docker-compose up -d fastapi-backend
```

## 6. Test Upload Flow

1. Open `frontend/index.html` in browser
2. Enter patient ID (e.g., "patient002")
3. Select a video/audio file
4. Click "Upload"
5. Check status in logs:
   ```bash
   docker-compose logs -f celery-worker
   ```

## 7. Monitor Background Jobs

```bash
# Open Flower dashboard
open http://localhost:5555

# Or check Celery directly
docker-compose exec celery-worker celery -A app.worker.celery_app inspect active
```

## 8. Troubleshooting

### Services Won't Start
```bash
# Check logs
docker-compose logs

# Check Docker resources
docker system df

# Restart Docker Desktop
```

### 502 Bad Gateway
```bash
# Check backend is running
docker-compose ps fastapi-backend

# Restart backend
docker-compose restart fastapi-backend
```

### Worker Not Processing Jobs
```bash
# Check Redis
docker-compose exec redis redis-cli ping

# Check worker logs
docker-compose logs -f celery-worker

# Restart worker
docker-compose restart celery-worker
```

### Out of Memory
```bash
# Check resource usage
docker stats

# Increase Docker memory limit in Docker Desktop settings
# Recommended: 8GB minimum
```

## 9. Development Workflow

### Make Code Changes
```bash
# 1. Edit code in backend/app/
vim backend/app/main.py

# 2. Rebuild
docker-compose build fastapi-backend

# 3. Restart
docker-compose up -d fastapi-backend

# 4. Check logs
docker-compose logs -f fastapi-backend
```

### Add Dependencies
```bash
# 1. Add to requirements.txt
echo "new-package==1.0.0" >> backend/app/requirements.txt

# 2. Rebuild
docker-compose build fastapi-backend

# 3. Restart
docker-compose up -d fastapi-backend
```

### Debug Issues
```bash
# Enter container shell
docker-compose exec fastapi-backend /bin/bash

# Check environment
env | grep AWS

# Test Python imports
python -c "from app.main import app; print(app)"

# Exit
exit
```

## 10. Production Deployment

### Enable SSL
```bash
# 1. Get SSL certificates
certbot certonly --webroot -w /var/www/certbot -d your-domain.com

# 2. Enable SSL config
cd infra/nginx/conf.d
cp ssl.conf.example ssl.conf
nano ssl.conf  # Update domain

# 3. Reload Nginx
docker-compose exec nginx nginx -s reload
```

### Deploy to EC2
```bash
# 1. SSH to EC2 instance
ssh -i key.pem ec2-user@your-instance-ip

# 2. Clone repository
git clone https://github.com/your-org/schizodot-ai-dot.git
cd schizodot-ai-dot

# 3. Configure environment
cp .env.example .env
nano .env

# 4. Start services
docker-compose up -d

# 5. Check status
docker-compose ps
```

## 11. Maintenance

### View Resource Usage
```bash
docker stats
```

### Clean Up
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove unused networks
docker network prune

# Full cleanup (CAUTION)
docker system prune -a --volumes
```

### Backup Data
```bash
# Backup uploads
tar -czf uploads-backup.tar.gz uploads/

# Backup logs
tar -czf logs-backup.tar.gz logs/

# Backup Redis
docker-compose exec redis redis-cli SAVE
docker cp schizodot-redis:/data/dump.rdb ./redis-backup.rdb
```

## 12. Getting Help

### Check Documentation
- [Docker Setup](./DOCKER_SETUP.md)
- [Nginx Configuration](../infra/nginx/README.md)
- [Docker README](../infra/docker/README.md)

### View Logs
```bash
docker-compose logs -f
```

### Check Service Health
```bash
docker-compose ps
curl http://localhost/health
curl http://localhost/api/v1/health
```

### Common Issues
1. **Port already in use**: Change ports in docker-compose.yml
2. **Out of memory**: Increase Docker memory limit
3. **AWS credentials invalid**: Check .env file
4. **Services not healthy**: Wait 1-2 minutes, check logs

## 13. Next Steps

After setup is complete:
1. ✅ Test upload flow with test video
2. ✅ Monitor Celery jobs in Flower
3. ✅ Check API documentation
4. ⏭️ Integrate with Lovable frontend
5. ⏭️ Enable AWS Bedrock for LLM analysis
6. ⏭️ Deploy to production EC2

---

**Need Help?**
- Check logs: `docker-compose logs -f`
- Run tests: `./scripts/test-full-stack.sh`
- Review docs in `docs/` directory
