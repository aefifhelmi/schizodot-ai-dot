#!/bin/bash
# ============================================
# Run Script - Real-Time Flask Proto
# ============================================
# Runs the real-time compliance monitoring UI

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

IMAGE_NAME="${IMAGE_NAME:-pill-detection-proto}"
CONTAINER_NAME="${CONTAINER_NAME:-pill-detection-proto}"
PORT="${PORT:-5001}"  # Changed from 5002 to 5001
VERSION="${VERSION:-latest}"

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🚀 Starting Real-Time Flask Proto Container              ║${NC}"
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
echo "  Port:       ${PORT} (Flask UI)"
echo ""

# Run container
# Note: Camera access in Docker on macOS is limited. For full camera support, run locally with python3 proto.py
docker run -d \
    --name "${CONTAINER_NAME}" \
    -p "${PORT}:5001" \
    -e TORCH_LOAD_WEIGHTS_ONLY=0 \
    --restart unless-stopped \
    "${IMAGE_NAME}:${VERSION}"

echo -e "${YELLOW}⏳ Waiting for Flask UI to start...${NC}"
echo "   (Model loading takes ~30-40 seconds)"
echo ""

# Wait for health check
for i in {1..60}; do
    if curl -sf http://localhost:${PORT}/status_update > /dev/null 2>&1; then
        echo ""
        echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║  ✅ Real-Time UI Ready!                                   ║${NC}"
        echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${GREEN}Flask UI Endpoints:${NC}"
        echo "  📍 Main UI:     http://localhost:${PORT}/"
        echo "  📹 Video Feed:  http://localhost:${PORT}/video_feed"
        echo "  📊 Status:      http://localhost:${PORT}/status_update"
        echo "  🎯 Start:       http://localhost:${PORT}/start_protocol"
        echo "  🛑 Stop:        http://localhost:${PORT}/stop_protocol"
        echo ""
        echo -e "${BLUE}Open in Browser:${NC}"
        echo "  open http://localhost:${PORT}/"
        echo ""
        echo -e "${BLUE}View Logs:${NC}"
        echo "  docker logs -f ${CONTAINER_NAME}"
        echo ""
        
        # Open in browser
        sleep 2
        open "http://localhost:${PORT}/" 2>/dev/null || true
        
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
echo -e "${RED}❌ Flask UI failed to start within 60 seconds${NC}"
echo ""
echo "Check logs:"
echo "  docker logs ${CONTAINER_NAME}"
echo ""
echo "Common issues:"
echo "  1. Model file corrupted"
echo "  2. Port ${PORT} already in use"
echo "  3. Insufficient memory"
echo ""
exit 1
