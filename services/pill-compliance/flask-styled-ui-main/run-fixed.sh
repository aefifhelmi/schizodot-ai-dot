#!/bin/bash
# ============================================
# FIXED Run Script - Pill Detection API
# ============================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

IMAGE_NAME="${IMAGE_NAME:-pill-detection-api-fixed}"
CONTAINER_NAME="${CONTAINER_NAME:-pill-detection-api-fixed}"
PORT="${PORT:-8003}"
VERSION="${VERSION:-latest}"

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🚀 Starting FIXED Pill Detection API Container           ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Stop existing container
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${YELLOW}⚠️  Stopping existing container...${NC}"
    docker stop "${CONTAINER_NAME}" 2>/dev/null || true
    docker rm "${CONTAINER_NAME}" 2>/dev/null || true
fi

echo -e "${GREEN}Starting container:${NC}"
echo "  Image:      ${IMAGE_NAME}:${VERSION}"
echo "  Container:  ${CONTAINER_NAME}"
echo "  Port:       ${PORT}"
echo ""

# Run container
docker run -d \
    --name "${CONTAINER_NAME}" \
    -p "${PORT}:8003" \
    -e MODEL_PATH=/app/models/best.pt \
    -e DEVICE=cpu \
    -e TORCH_LOAD_WEIGHTS_ONLY=0 \
    --restart unless-stopped \
    "${IMAGE_NAME}:${VERSION}"

echo -e "${YELLOW}⏳ Waiting for API to initialize...${NC}"
echo "   (Model loading takes ~30-40 seconds)"
echo ""

# Wait for health check
for i in {1..60}; do
    if curl -sf http://localhost:${PORT}/health > /dev/null 2>&1; then
        echo ""
        echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║  ✅ API Ready!                                            ║${NC}"
        echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${GREEN}API Endpoints:${NC}"
        echo "  📍 Root:        http://localhost:${PORT}/"
        echo "  💚 Health:      http://localhost:${PORT}/health"
        echo "  🔍 Detect:      http://localhost:${PORT}/v1/detect"
        echo "  📊 Model Info:  http://localhost:${PORT}/v1/model/info"
        echo "  📖 API Docs:    http://localhost:${PORT}/docs"
        echo ""
        echo -e "${BLUE}Test Commands:${NC}"
        echo "  # Health check"
        echo "  curl http://localhost:${PORT}/health | jq ."
        echo ""
        echo "  # Model info"
        echo "  curl http://localhost:${PORT}/v1/model/info | jq ."
        echo ""
        echo "  # Detect compliance"
        echo '  curl -X POST "http://localhost:'${PORT}'/v1/detect" \'
        echo '       -F "video=@your-video.mp4" | jq .'
        echo ""
        echo -e "${BLUE}View Logs:${NC}"
        echo "  docker logs -f ${CONTAINER_NAME}"
        echo ""
        echo -e "${BLUE}Run Tests:${NC}"
        echo "  ./test-fixed.sh"
        echo ""
        exit 0
    fi
    
    # Show progress
    if [ $((i % 5)) -eq 0 ]; then
        echo "   Still loading... ($i seconds elapsed)"
    else
        echo -n "."
    fi
    sleep 1
done

echo ""
echo -e "${RED}❌ API failed to start within 60 seconds${NC}"
echo ""
echo "Check logs:"
echo "  docker logs ${CONTAINER_NAME}"
echo ""
echo "Common issues:"
echo "  1. Model file corrupted or wrong format"
echo "  2. Insufficient memory (need ~2GB)"
echo "  3. Port ${PORT} already in use"
echo ""
exit 1
