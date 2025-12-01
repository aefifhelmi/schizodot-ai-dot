# SchizoDot AI - Developer Setup Guide

Complete guide for setting up the SchizoDot AI development environment on **macOS**, **Linux**, and **Windows**.

---

## Prerequisites

### Required Software

| Software | Version | Download |
|----------|---------|----------|
| Docker Desktop | 20.10+ | [docker.com/get-docker](https://docs.docker.com/get-docker/) |
| Git | 2.30+ | [git-scm.com](https://git-scm.com/downloads) |
| Python | 3.9+ | [python.org](https://www.python.org/downloads/) (for frontend servers) |

### System Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 4 cores | 8 cores |
| RAM | 8 GB | 16 GB |
| Storage | 20 GB | 40 GB |

### AWS Requirements

You need AWS credentials with access to:
- **S3 Bucket**: `schizodot-backend-storage`
- **DynamoDB Tables**: `SchizodotUsers`, `SchizodotJobs`

---

## Quick Start

### macOS / Linux

```bash
# 1. Clone the repository
git clone https://github.com/aefifhelmi/schizodot-ai-dot.git
cd schizodot-ai-dot
git checkout dev

# 2. Run setup script
./scripts/setup.sh

# 3. Edit .env with your AWS credentials
nano .env  # or use your preferred editor

# 4. Build and start services
docker compose build
docker compose up -d

# 5. Verify all services are running
docker compose ps
```

### Windows (PowerShell)

```powershell
# 1. Clone the repository
git clone https://github.com/aefifhelmi/schizodot-ai-dot.git
cd schizodot-ai-dot
git checkout dev

# 2. Run setup script (in PowerShell)
.\scripts\setup.ps1

# 3. Edit .env with your AWS credentials
notepad .env

# 4. Build and start services
docker compose build
docker compose up -d

# 5. Verify all services are running
docker compose ps
```

---

## Windows-Specific Setup

### 1. Install Docker Desktop for Windows

1. Download from [docker.com/desktop/windows](https://docs.docker.com/desktop/install/windows-install/)
2. During installation, select **"Use WSL 2 instead of Hyper-V"** (recommended)
3. After installation, open Docker Desktop and wait for it to start

### 2. Enable WSL2 (Recommended)

```powershell
# Run in PowerShell as Administrator
wsl --install
wsl --set-default-version 2
```

### 3. Configure Docker Desktop

1. Open Docker Desktop → Settings
2. Go to **Resources** → **WSL Integration**
3. Enable integration with your WSL distro
4. Go to **Resources** → **Advanced**
   - Set Memory: 8 GB minimum
   - Set CPUs: 4 minimum

### 4. Handle Port Conflicts

Windows may have services using required ports:

| Port | Common Conflict | Solution |
|------|-----------------|----------|
| 80 | IIS | `iisreset /stop` or change nginx port |
| 5000 | Windows services | Change proto-compliance port |
| 8000 | Other apps | Stop conflicting app |

To check port usage:
```powershell
netstat -ano | findstr :80
netstat -ano | findstr :8000
```

### 5. Line Ending Issues

If you see errors about line endings, run:
```bash
git config --global core.autocrlf input
git checkout -- .
```

---

## Environment Configuration

### Create .env File

```bash
cp .env.example .env
```

### Required Variables

Edit `.env` and set these values:

```env
# AWS Credentials (REQUIRED)
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1

# S3 and DynamoDB
S3_BUCKET=schizodot-backend-storage
DYNAMO_TABLE=SchizodotUsers
DYNAMO_TABLE_JOBS=SchizodotJobs

# Optional: Enable Bedrock LLM
BEDROCK_ENABLE=false
```

---

## Model Files

The following model files are required and should be included in the repository:

### Emotion Detection Models
```
services/emotion-detection/schizodot_emotion_demo/ai/emotion/weights/
├── audio_model.pkl
└── audio_label_encoder.pkl
```

### Pill Detection Model
```
flask-styled-ui-main/models/
└── best.pt
```

> **Note**: If these files are missing after clone, contact the team lead.

---

## Running the Services

### Start All Services

```bash
docker compose up -d
```

### Check Service Status

```bash
docker compose ps
```

All services should show `healthy`:

| Service | Port | Description |
|---------|------|-------------|
| fastapi-backend | 8000 | Main API |
| emotion-service | 8001 | Emotion AI |
| pill-detection | 8003 | Pill detection AI |
| proto-compliance | 5001 | Live compliance |
| redis | 6379 | Message queue |
| celery-worker | - | Background tasks |
| nginx | 80 | Reverse proxy |
| flower | 5555 | Celery monitor |

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f fastapi-backend
```

### Stop Services

```bash
docker compose down
```

---

## Running Frontend Applications

Open **two separate terminals**:

### Terminal 1: Patient Portal

```bash
cd frontend/patient-portal
python3 -m http.server 3000
```
Access: http://localhost:3000/index-new.html

### Terminal 2: Clinician Dashboard

```bash
cd frontend/clinician-dashboard
python3 -m http.server 3001
```
Access: http://localhost:3001/index-new.html

---

## Service URLs

| Service | URL |
|---------|-----|
| Backend API | http://localhost:8000/api/v1 |
| API Documentation | http://localhost:8000/docs |
| Emotion Service | http://localhost:8001 |
| Pill Detection | http://localhost:8003 |
| Proto Compliance | http://localhost:5001 |
| Flower (Celery UI) | http://localhost:5555 |
| Patient Portal | http://localhost:3000/index-new.html |
| Clinician Dashboard | http://localhost:3001/index-new.html |

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs for the failing service
docker compose logs <service-name>

# Rebuild the service
docker compose up -d --build <service-name>
```

### Port Already in Use

```bash
# Find what's using the port (macOS/Linux)
lsof -i :8000

# Find what's using the port (Windows)
netstat -ano | findstr :8000

# Kill the process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows
```

### Docker Out of Space

```bash
# Clean up unused images and containers
docker system prune -a
```

### Permission Denied (Linux)

```bash
sudo chown -R $USER:$USER uploads logs
```

### Model File Missing

If you see errors about missing `.pkl` or `.pt` files:
1. Check if files exist in the correct directories
2. If missing, contact team lead for the model files
3. Place files in the correct locations as shown above

---

## Development Workflow

### Rebuilding After Code Changes

```bash
# Rebuild specific service
docker compose up -d --build fastapi-backend

# Rebuild all services
docker compose up -d --build
```

### Accessing Container Shell

```bash
docker exec -it schizodot-fastapi /bin/bash
```

### Running Tests

```bash
# Run tests inside container
docker exec -it schizodot-fastapi pytest
```

---

## Getting Help

1. Check service logs: `docker compose logs <service>`
2. Check Docker Desktop for resource issues
3. Verify AWS credentials are correct
4. Contact team lead for model files or AWS access

---

**Last Updated**: December 2025
