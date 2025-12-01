#!/bin/bash
# ============================================
# SchizoDot AI - Setup Script (macOS/Linux)
# ============================================

set -e

echo "============================================"
echo "  SchizoDot AI - Development Setup"
echo "============================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if Docker is installed
echo "Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker Desktop first."
    echo "  Download: https://docs.docker.com/get-docker/"
    exit 1
fi
print_status "Docker is installed"

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker Desktop."
    exit 1
fi
print_status "Docker is running"

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not available."
    exit 1
fi
print_status "Docker Compose is available"

echo ""
echo "Setting up project..."

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        print_warning ".env file created from .env.example"
        echo "  Please edit .env and add your AWS credentials before running Docker."
    else
        print_error ".env.example not found!"
        exit 1
    fi
else
    print_status ".env file exists"
fi

# Create required directories
mkdir -p uploads logs logs/nginx
print_status "Created uploads/ and logs/ directories"

# Check for model files
echo ""
echo "Checking model files..."

EMOTION_WEIGHTS_DIR="services/emotion-detection/schizodot_emotion_demo/ai/emotion/weights"
PILL_MODELS_DIR="flask-styled-ui-main/models"

if [ -f "$EMOTION_WEIGHTS_DIR/audio_model.pkl" ] && [ -f "$EMOTION_WEIGHTS_DIR/audio_label_encoder.pkl" ]; then
    print_status "Emotion model weights found"
else
    print_error "Emotion model weights missing!"
    echo "  Required files:"
    echo "    - $EMOTION_WEIGHTS_DIR/audio_model.pkl"
    echo "    - $EMOTION_WEIGHTS_DIR/audio_label_encoder.pkl"
    echo "  Contact the team lead to obtain these files."
fi

if [ -f "$PILL_MODELS_DIR/best.pt" ]; then
    print_status "Pill detection model found"
else
    print_error "Pill detection model missing!"
    echo "  Required file: $PILL_MODELS_DIR/best.pt"
    echo "  Contact the team lead to obtain this file."
fi

echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Edit .env file with your AWS credentials"
echo "  2. Run: docker compose build"
echo "  3. Run: docker compose up -d"
echo "  4. Check status: docker compose ps"
echo ""
echo "Service URLs after startup:"
echo "  - Backend API:        http://localhost:8000/api/v1"
echo "  - API Docs:           http://localhost:8000/docs"
echo "  - Emotion Service:    http://localhost:8001"
echo "  - Pill Detection:     http://localhost:8003"
echo "  - Proto Compliance:   http://localhost:5001"
echo "  - Flower (Celery):    http://localhost:5555"
echo ""
echo "Frontend (run separately):"
echo "  - Patient Portal:     cd frontend/patient-portal && python3 -m http.server 3000"
echo "  - Clinician Dashboard: cd frontend/clinician-dashboard && python3 -m http.server 3001"
echo ""
