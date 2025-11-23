# 🧪 Testing Guide - Fixed Docker Container

This guide explains how to test the fixed containerization after resolving all dependency and compatibility issues.

---

## ⚡ Quick Test (When Docker is Running)

```bash
cd /Users/tengkuafif/schizodot-ai-dot/flask-styled-ui-main

# Build
./build-fixed.sh

# Run
./run-fixed.sh

# Test
./test-fixed.sh
```

**Expected Result**: All tests pass ✅

---

## 📋 Manual Testing Steps

### Step 1: Pre-Build Validation

Before building, verify all files are present:

```bash
cd /Users/tengkuafif/schizodot-ai-dot/flask-styled-ui-main

# Check model file
ls -lh models/best.pt
# Expected: ~18MB file

# Check fixed requirements
cat requirements-fixed.txt
# Should show all pinned versions

# Check Dockerfile
cat Dockerfile.fixed
# Should handle torch separately and install system deps
```

---

### Step 2: Build the Image

```bash
./build-fixed.sh
```

**Expected Output**:
```
╔═══════════════════════════════════════════════════════════╗
║  🐳 Building FIXED Pill Detection API Container          ║
╚═══════════════════════════════════════════════════════════╝

Configuration:
  Image Name:    pill-detection-api-fixed
  Version:       1.0.0
  ...

📋 Pre-build validation...
  ✅ Model file found (18M)
  ✅ Requirements file found
  ✅ Detector script found
  ✅ API service found

🔨 Building Docker image...
[build output...]

╔═══════════════════════════════════════════════════════════╗
║  ✅ Build Successful!                                     ║
╚═══════════════════════════════════════════════════════════╝

Tagged images:
  📦 pill-detection-api-fixed:1.0.0
  📦 pill-detection-api-fixed:latest

  📊 Image size: ~1.8GB

Next steps:
  1. Test locally:  ./run-fixed.sh
```

**Common Build Issues**:

| Issue | Solution |
|-------|----------|
| "Cannot connect to Docker daemon" | Start Docker Desktop |
| "models/best.pt not found" | Ensure model file is in models/ |
| "pip install failed" | Check internet connection |
| "Platform mismatch" | Build is for linux/amd64, normal if on Mac |

---

### Step 3: Run the Container

```bash
./run-fixed.sh
```

**Expected Output**:
```
╔═══════════════════════════════════════════════════════════╗
║  🚀 Starting FIXED Pill Detection API Container           ║
╚═══════════════════════════════════════════════════════════╝

Starting container:
  Image:      pill-detection-api-fixed:latest
  Container:  pill-detection-api-fixed
  Port:       8003

⏳ Waiting for API to initialize...
   (Model loading takes ~30-40 seconds)

   Still loading... (5 seconds elapsed)
   Still loading... (10 seconds elapsed)
   ...
   Still loading... (35 seconds elapsed)

╔═══════════════════════════════════════════════════════════╗
║  ✅ API Ready!                                            ║
╚═══════════════════════════════════════════════════════════╝

API Endpoints:
  📍 Root:        http://localhost:8003/
  💚 Health:      http://localhost:8003/health
  🔍 Detect:      http://localhost:8003/v1/detect
  📊 Model Info:  http://localhost:8003/v1/model/info
  📖 API Docs:    http://localhost:8003/docs
```

**Common Startup Issues**:

| Issue | Cause | Solution |
|-------|-------|----------|
| Times out after 60s | Model file corrupted | Re-download model |
| "Port 8003 already in use" | Another service running | Change PORT env var |
| Container exits immediately | Dependency error | Check logs: `docker logs pill-detection-api-fixed` |
| OOM (out of memory) | Insufficient RAM | Allocate 4GB+ to Docker |

---

### Step 4: Manual API Tests

Once container is running, test endpoints manually:

#### Test 1: Health Check
```bash
curl http://localhost:8003/health | jq .
```

**Expected Response**:
```json
{
  "status": "healthy",
  "service": "pill-detection",
  "model_loaded": true,
  "model_path": "/app/models/best.pt",
  "timestamp": "2025-11-19T09:00:00.000000"
}
```

#### Test 2: Root Endpoint
```bash
curl http://localhost:8003/ | jq .
```

**Expected Response**:
```json
{
  "service": "pill-detection",
  "version": "1.0.0",
  "status": "healthy",
  "endpoints": {
    "health": "/health",
    "detect": "/v1/detect"
  }
}
```

#### Test 3: Model Info
```bash
curl http://localhost:8003/v1/model/info | jq .
```

**Expected Response**:
```json
{
  "model_type": "YOLOv11",
  "framework": "Ultralytics",
  "classes": ["pill", "pill-on-tongue", "tongue-no-pill", "hand"],
  "thresholds": {
    "pill": 0.7,
    "pill-on-tongue": 0.4,
    "tongue-no-pill": 0.5,
    "hand": 0.75
  },
  "model_path": "/app/models/best.pt"
}
```

#### Test 4: API Documentation
Open in browser:
```
http://localhost:8003/docs
```

Should see **Swagger UI** with interactive API documentation.

---

### Step 5: Automated Test Suite

Run the comprehensive test suite:

```bash
./test-fixed.sh
```

**Expected Output**:
```
╔══════════════════════════════════════════════════════════╗
║  🧪 PILL DETECTION API - VALIDATION TESTS                ║
╚══════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════
TEST 1: Container Status
═══════════════════════════════════════════════════════════

Testing: Container is running... ✅ PASS
Testing: Container health status... ✅ PASS

═══════════════════════════════════════════════════════════
TEST 2: API Endpoints
═══════════════════════════════════════════════════════════

Testing: Root endpoint (GET /)... ✅ PASS
Testing: Health endpoint (GET /health)... ✅ PASS
Testing: API docs (GET /docs)... ✅ PASS
Testing: Model info endpoint (GET /v1/model/info)... ✅ PASS

═══════════════════════════════════════════════════════════
TEST 3: API Response Structure
═══════════════════════════════════════════════════════════

Testing: Health check returns JSON... ✅ PASS
Testing: Health status is 'healthy'... ✅ PASS
Testing: Model is loaded... ✅ PASS
Testing: Model info has classes... ✅ PASS
   📊 Model classes: pill, pill-on-tongue, tongue-no-pill, hand

═══════════════════════════════════════════════════════════
TEST 4: Container Logs
═══════════════════════════════════════════════════════════

Testing: No critical errors in logs... ✅ PASS
Testing: Model loaded successfully... ✅ PASS
Testing: MediaPipe initialized... ✅ PASS
Testing: API server started... ✅ PASS

═══════════════════════════════════════════════════════════
TEST 5: Resource Usage
═══════════════════════════════════════════════════════════

  📊 Memory: 1.8GiB / 7.7GiB
  📊 CPU: 2.5%
  ✅ Memory usage is reasonable

═══════════════════════════════════════════════════════════
TEST RESULTS
═══════════════════════════════════════════════════════════

✅ Passed: 16
❌ Failed: 0

🎉 ALL TESTS PASSED!

✅ Container is working correctly
✅ Model is loaded and ready
✅ API endpoints are responding
✅ Resource usage is normal

Ready for production testing!
```

---

### Step 6: Video Detection Test

Test actual pill detection with a video:

```bash
# Create a test video or use existing one
curl -X POST "http://localhost:8003/v1/detect" \
     -F "video=@/path/to/test-video.mp4" \
     | jq .
```

**Expected Response**:
```json
{
  "compliance_score": 95.5,
  "verification_status": "PASSED",
  "phases_completed": 6,
  "protocol_status": "PASSED",
  "detected_objects": [
    {
      "class": "pill",
      "confidence": 0.92,
      "count": 45
    },
    {
      "class": "hand",
      "confidence": 0.87,
      "count": 38
    }
  ],
  "phase_details": {
    "phase_1": {"status": "PASSED", "frames": 45},
    "phase_2": {"status": "PASSED", "frames": 38},
    ...
  },
  "filename": "test-video.mp4",
  "processing_time_ms": 2340,
  "timestamp": "2025-11-19T09:00:00.000000"
}
```

---

## 🔍 Debugging Failed Tests

### View Container Logs

```bash
docker logs pill-detection-api-fixed

# Follow logs in real-time
docker logs -f pill-detection-api-fixed

# Last 50 lines
docker logs --tail 50 pill-detection-api-fixed
```

**What to look for**:
- ✅ "YOLOv11 model loaded successfully"
- ✅ "MediaPipe Face Mesh initialized"
- ✅ "Application startup complete"
- ❌ Any lines containing "ERROR" or "FAILED"

### Inspect Container

```bash
# Check if container is running
docker ps -a | grep pill-detection

# Get container details
docker inspect pill-detection-api-fixed

# Execute commands inside container
docker exec -it pill-detection-api-fixed bash

# Inside container, test Python imports
python -c "import torch; print(torch.__version__)"
python -c "from ultralytics import YOLO; print('✅ YOLO imported')"
python -c "import mediapipe; print('✅ MediaPipe imported')"
python -c "import cv2; print(cv2.__version__)"
```

### Check Health Status

```bash
# Docker health check
docker inspect --format='{{.State.Health.Status}}' pill-detection-api-fixed

# Manual health check
curl http://localhost:8003/health
```

### Resource Monitoring

```bash
# Real-time stats
docker stats pill-detection-api-fixed

# One-time stats
docker stats --no-stream pill-detection-api-fixed
```

---

## 📊 Validation Checklist

Before considering the container production-ready, verify:

### Build Phase
- [ ] Build completes without errors
- [ ] All dependencies install successfully
- [ ] torch 2.8.0 installs (CPU version)
- [ ] Image size is reasonable (~1.8GB)
- [ ] No security vulnerabilities in base image

### Startup Phase
- [ ] Container starts without crashes
- [ ] Model loads within 40 seconds
- [ ] MediaPipe initializes successfully
- [ ] Health check passes
- [ ] No error messages in logs

### API Phase
- [ ] All endpoints return 200 OK
- [ ] JSON responses are valid
- [ ] Model info shows correct classes
- [ ] Interactive docs accessible at /docs

### Detection Phase
- [ ] Video upload works
- [ ] Detection completes in < 10 seconds
- [ ] Response includes all required fields
- [ ] Compliance score is 0-100
- [ ] Detected objects list is populated

### Performance Phase
- [ ] Memory usage < 2.5GB
- [ ] CPU usage < 10% at idle
- [ ] Startup time < 45 seconds
- [ ] Detection time < 10s per video
- [ ] No memory leaks over time

### Security Phase
- [ ] Container runs as non-root user
- [ ] No sensitive data in logs
- [ ] Health endpoint doesn't expose secrets
- [ ] File permissions are correct

---

## 🚀 Next Steps After Validation

Once all tests pass:

1. **Tag for Production**
   ```bash
   docker tag pill-detection-api-fixed:latest \
              your-registry.com/pill-detection-api:1.0.0
   ```

2. **Push to Registry**
   ```bash
   docker push your-registry.com/pill-detection-api:1.0.0
   ```

3. **Deploy to Production**
   ```bash
   docker run -d \
     --name pill-detection-api \
     -p 8003:8003 \
     --restart unless-stopped \
     your-registry.com/pill-detection-api:1.0.0
   ```

4. **Set Up Monitoring**
   - Configure health checks
   - Set up logging aggregation
   - Add performance metrics
   - Create alerts for failures

---

## 📞 Support

If tests fail:
1. Check `DOCKER_DIAGNOSIS.md` for known issues
2. Review container logs
3. Verify Docker has sufficient resources (4GB+ RAM)
4. Ensure model file is not corrupted

---

**All tests passing? 🎉 Your container is production-ready!**
