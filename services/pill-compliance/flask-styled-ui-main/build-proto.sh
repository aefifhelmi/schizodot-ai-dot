#!/bin/bash
# ============================================
# Build Script - Real-Time Flask Proto
# ============================================
# Builds the real-time compliance monitoring UI

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

IMAGE_NAME="${IMAGE_NAME:-pill-detection-proto}"
VERSION="${VERSION:-1.0.0}"

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🐳 Building Real-Time Flask Proto Container             ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Configuration:${NC}"
echo "  Image Name:    ${IMAGE_NAME}"
echo "  Version:       ${VERSION}"
echo "  Type:          Real-Time UI with Camera"
echo ""

# Pre-build validation
echo -e "${YELLOW}📋 Pre-build validation...${NC}"

if [ ! -f "models/best.pt" ]; then
    echo -e "${RED}❌ Error: models/best.pt not found!${NC}"
    exit 1
fi
echo "  ✅ Model file found ($(ls -lh models/best.pt | awk '{print $5}'))"

if [ ! -f "proto.py" ]; then
    echo -e "${RED}❌ Error: proto.py not found!${NC}"
    exit 1
fi
echo "  ✅ Proto.py found"

if [ ! -f "requirements-proto.txt" ]; then
    echo -e "${RED}❌ Error: requirements-proto.txt not found!${NC}"
    exit 1
fi
echo "  ✅ Requirements file found"

echo ""
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
echo ""

# Temporarily replace .dockerignore with proto-specific one
if [ -f ".dockerignore" ]; then
    mv .dockerignore .dockerignore.backup
fi
if [ -f ".dockerignore.proto" ]; then
    cp .dockerignore.proto .dockerignore
fi

# Build image (disable BuildKit to avoid credential issues)
export DOCKER_BUILDKIT=0

docker build \
    -f Dockerfile.proto \
    -t "${IMAGE_NAME}:${VERSION}" \
    -t "${IMAGE_NAME}:latest" \
    . 2>&1 | tee build-proto.log

BUILD_EXIT=$?

# Restore original .dockerignore
if [ -f ".dockerignore.backup" ]; then
    mv .dockerignore.backup .dockerignore
fi

if [ $BUILD_EXIT -eq 0 ]; then
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
    echo "  1. Run container:  ./run-proto.sh"
    echo "  2. View logs:      cat build-proto.log"
    echo ""
else
    echo ""
    echo -e "${RED}❌ Build failed!${NC}"
    echo "Check build-proto.log for details"
    exit 1
fi
