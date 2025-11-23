#!/bin/bash
# ============================================
# FIXED Build Script - Pill Detection API
# ============================================
# Builds container with resolved dependencies

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

IMAGE_NAME="${IMAGE_NAME:-pill-detection-api-fixed}"
VERSION="${VERSION:-1.0.0}"
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🐳 Building FIXED Pill Detection API Container          ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Configuration:${NC}"
echo "  Image Name:    ${IMAGE_NAME}"
echo "  Version:       ${VERSION}"
echo "  Build Date:    ${BUILD_DATE}"
echo "  Git Commit:    ${GIT_COMMIT}"
echo ""

# Pre-build validation
echo -e "${YELLOW}📋 Pre-build validation...${NC}"

if [ ! -f "models/best.pt" ]; then
    echo -e "${RED}❌ Error: models/best.pt not found!${NC}"
    exit 1
fi
echo "  ✅ Model file found ($(ls -lh models/best.pt | awk '{print $5}'))"

if [ ! -f "requirements-fixed.txt" ]; then
    echo -e "${RED}❌ Error: requirements-fixed.txt not found!${NC}"
    exit 1
fi
echo "  ✅ Requirements file found"

if [ ! -f "simple_detector.py" ]; then
    echo -e "${RED}❌ Error: simple_detector.py not found!${NC}"
    exit 1
fi
echo "  ✅ Detector script found"

if [ ! -f "api_service.py" ]; then
    echo -e "${RED}❌ Error: api_service.py not found!${NC}"
    exit 1
fi
echo "  ✅ API service found"

echo ""
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
echo ""

# Build image
docker build \
    -f Dockerfile.fixed \
    -t "${IMAGE_NAME}:${VERSION}" \
    -t "${IMAGE_NAME}:latest" \
    --build-arg BUILD_DATE="${BUILD_DATE}" \
    --build-arg VERSION="${VERSION}" \
    --build-arg GIT_COMMIT="${GIT_COMMIT}" \
    --platform linux/amd64 \
    --progress=plain \
    . 2>&1 | tee build-fixed.log

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ Build Successful!                                     ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}Tagged images:${NC}"
    echo "  📦 ${IMAGE_NAME}:${VERSION}"
    echo "  📦 ${IMAGE_NAME}:latest"
    echo ""
    
    # Show image size
    SIZE=$(docker images --format "{{.Size}}" "${IMAGE_NAME}:latest" | head -1)
    echo "  📊 Image size: ${SIZE}"
    echo ""
    
    echo -e "${BLUE}Next steps:${NC}"
    echo "  1. Test locally:  ./run-fixed.sh"
    echo "  2. Run tests:     ./test-fixed.sh"
    echo "  3. View logs:     cat build-fixed.log"
    echo ""
else
    echo ""
    echo -e "${RED}❌ Build failed!${NC}"
    echo "Check build-fixed.log for details"
    exit 1
fi
