# Services

Microservices for AI analysis and specialized processing.

## Available Services

### 1. Emotion Detection (`emotion-detection/`)
**Port**: 5000  
**Technology**: Python, FastAPI, PyTorch

**Purpose**: Analyzes audio and facial emotions from video uploads

**Endpoints**:
- `POST /analyze` - Analyze video for emotions
- `GET /health` - Health check

**Models**:
- Audio: Wav2Vec2 fine-tuned for emotion recognition
- Facial: Computer vision model for facial emotion detection
- Fusion: Multimodal emotion fusion algorithm

**Start**:
```bash
cd emotion-detection
docker build -t emotion-service .
docker run -p 5000:5000 emotion-service
```

### 2. Pill Compliance (`pill-compliance/`)
**Port**: 5001  
**Technology**: Python, Flask, OpenCV, MediaPipe

**Purpose**: Real-time medication compliance verification using computer vision

**Features**:
- 6-phase compliance protocol
- Hand detection
- Face detection
- Pill detection
- Swallow verification

**Phases**:
1. Show pill in hand
2. Open mouth + show tongue
3. Place pill on tongue
4. Close mouth
5. Swallow
6. Open mouth (verify empty)

**Start**:
```bash
cd pill-compliance
python proto.py
# Access at http://localhost:5001
```

**Endpoints**:
- `GET /` - Web interface with camera access
- `POST /video_feed` - Real-time video stream
- `GET /status_update` - Protocol status (JSON)

## Service Integration

All services integrate with the main backend API:

```
Patient Portal → Backend API → Services → Results Storage
                      ↓
                 DynamoDB/S3
```

## Development

### Running All Services with Docker Compose
```bash
# From project root
docker-compose up -d
```

### Running Individual Services

**Emotion Service**:
```bash
cd services/emotion-detection
pip install -r requirements.txt
uvicorn main:app --port 5000
```

**Pill Compliance**:
```bash
cd services/pill-compliance
pip install -r requirements.txt
python proto.py
```

## Testing Services

### Test Emotion Service
```bash
curl -X POST http://localhost:5000/analyze \
  -F "video=@test_video.webm"
```

### Test Pill Compliance
```bash
# Open browser to http://localhost:5001
# Or check status:
curl http://localhost:5001/status_update
```

## Environment Variables

### Emotion Service
```env
MODEL_PATH=/app/models
DEVICE=cuda  # or cpu
LOG_LEVEL=INFO
```

### Pill Compliance
```env
CAMERA_INDEX=0
CONFIDENCE_THRESHOLD=0.7
PORT=5001
```

## Monitoring

Check service health:
```bash
# Emotion service
curl http://localhost:5000/health

# Pill compliance
curl http://localhost:5001/status_update
```

## Deployment

### Docker
Each service has its own Dockerfile and can be deployed independently.

### AWS
- Deploy on ECS/Fargate
- Use Application Load Balancer
- Store models in S3
- Use CloudWatch for monitoring

## Troubleshooting

**Problem**: Emotion service GPU errors  
**Solution**: Set `DEVICE=cpu` or install CUDA drivers

**Problem**: Pill compliance camera not working  
**Solution**: Grant camera permissions in browser, check CAMERA_INDEX

**Problem**: Services not reachable  
**Solution**: Check firewall rules, verify ports are exposed

## Performance

- **Emotion Detection**: ~5-10s per video
- **Pill Compliance**: Real-time (30 FPS)

## Security

- Services run in isolated containers
- No direct internet exposure (behind API gateway)
- Input validation on all endpoints
- Rate limiting enabled
