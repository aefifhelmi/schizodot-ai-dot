# ============================================
# Emotion Service Dockerfile
# ============================================
# Complete multimodal emotion detection with audio + face (FER)

FROM python:3.9-slim

# Set metadata
LABEL maintainer="SchizoDot AI Team"
LABEL description="Emotion Detection Service - Audio + Face (FER)"
LABEL version="2.0.0"

# Set environment variables for headless operation
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    # Matplotlib backend for headless
    MPLBACKEND=Agg \
    # TensorFlow settings
    TF_CPP_MIN_LOG_LEVEL=2 \
    # OpenCV headless mode
    OPENCV_VIDEOIO_DEBUG=0 \
    QT_QPA_PLATFORM=offscreen \
    # Disable interactive displays
    DISPLAY=

WORKDIR /app

# Install system dependencies
# - ffmpeg: audio extraction
# - OpenCV dependencies: libsm6, libxext6, libxrender-dev, libgomp1
# - Audio processing: libsndfile1
# - Build tools: gcc, g++ for some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libsndfile1 \
    curl \
    wget \
    ca-certificates \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 emotionuser && \
    chown -R emotionuser:emotionuser /app

# Copy requirements first for better caching
COPY --chown=emotionuser:emotionuser backend/services/emotion/requirements.txt /app/requirements.txt

# Install Python dependencies
# Install with increased timeout for packages like tensorflow
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --timeout 300 -r /app/requirements.txt

# Copy application code
COPY --chown=emotionuser:emotionuser backend /app/backend

# Copy AI model weights
COPY --chown=emotionuser:emotionuser ai/emotion/weights /app/ai/emotion/weights

# Create necessary directories
RUN mkdir -p /app/uploads /app/logs /app/tmp && \
    chown -R emotionuser:emotionuser /app/uploads /app/logs /app/tmp

# Switch to non-root user
USER emotionuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the emotion service
CMD ["uvicorn", "backend.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--log-level", "info"]
