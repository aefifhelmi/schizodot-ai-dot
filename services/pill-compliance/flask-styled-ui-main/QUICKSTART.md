# ⚡ Quick Start - Pill Detection API

## One Command Deployment

```bash
./build.sh && ./run.sh
```

**That's it!** API is now running at `http://localhost:8003`

---

## 📋 Command Reference

### Local Development

```bash
# Build image
./build.sh

# Run container
./run.sh

# Test API
curl http://localhost:8003/health

# View logs
docker logs -f pill-detection-api

# Stop container
docker stop pill-detection-api
```

### Production Deployment

```bash
# 1. Set registry
export REGISTRY="your-registry.com/"
export VERSION="1.0.0"

# 2. Build
./build.sh

# 3. Push to registry
./push.sh

# 4. Deploy
docker run -d \
  --name pill-detection-api \
  -p 8003:8003 \
  --restart unless-stopped \
  your-registry.com/pill-detection-api:1.0.0
```

### Test Detection

```bash
# Upload video for compliance check
curl -X POST "http://localhost:8003/v1/detect" \
     -F "video=@test-video.mp4" \
     | jq .
```

---

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VERSION` | `latest` | Image version tag |
| `PORT` | `8003` | API port |
| `REGISTRY` | (empty) | Registry URL for push |
| `IMAGE_NAME` | `pill-detection-api` | Image name |
| `DEVICE` | `cpu` | Inference device |

---

## 📚 Full Documentation

See [DEPLOYMENT.md](DEPLOYMENT.md) for:
- ✅ Complete acceptance checklist
- 📖 API reference
- 🚀 Kubernetes deployment
- 🔧 Troubleshooting guide
- 📌 Version management

---

## ✅ Pre-flight Checklist

- [ ] Model file exists: `models/best.pt`
- [ ] Docker is running: `docker ps`
- [ ] Scripts are executable: `ls -l *.sh`

---

## 🎯 Expected Response

```json
{
  "compliance_score": 95.5,
  "verification_status": "PASSED",
  "phases_completed": 6,
  "protocol_status": "PASSED",
  "processing_time_ms": 2340
}
```

---

**Need help?** Check [DEPLOYMENT.md](DEPLOYMENT.md) or open an issue.
