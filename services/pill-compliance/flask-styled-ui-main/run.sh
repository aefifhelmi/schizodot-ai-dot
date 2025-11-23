#!/bin/bash
# ============================================
# Run Script - Pill Detection API (Local)
# ============================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
IMAGE_NAME="${IMAGE_NAME:-pill-detection-api}"
CONTAINER_NAME="${CONTAINER_NAME:-pill-detection-api}"
PORT="${PORT:-8003}"
VERSION="${VERSION:-latest}"

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🚀 Starting Pill Detection API Container                 ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Stop existing container if running
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

# Wait for container to be healthy
echo -e "${YELLOW}⏳ Waiting for API to be ready...${NC}"
sleep 5

# Check health
for i in {1..30}; do
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
        echo -e "${BLUE}View logs:${NC}"
        echo "  docker logs -f ${CONTAINER_NAME}"
        echo ""
        echo -e "${BLUE}Test the API:${NC}"
        echo '  curl -X POST "http://localhost:'${PORT}'/v1/detect" \'
        echo '       -F "video=@your-video.mp4"'
        echo ""
        exit 0
    fi
    echo -n "."
    sleep 2
done

echo ""
echo -e "${RED}❌ API failed to start. Check logs:${NC}"
echo "  docker logs ${CONTAINER_NAME}"
exit 1
