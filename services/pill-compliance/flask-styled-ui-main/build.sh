#!/bin/bash
# ============================================
# Build Script - Pill Detection API
# ============================================
# Semantic versioning with build metadata

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="${IMAGE_NAME:-pill-detection-api}"
REGISTRY="${REGISTRY:-}"  # Empty for local, set to "your-registry.com/" for remote
VERSION="${VERSION:-1.0.0}"
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Construct full image name
if [ -n "$REGISTRY" ]; then
    FULL_IMAGE="${REGISTRY}${IMAGE_NAME}"
else
    FULL_IMAGE="${IMAGE_NAME}"
fi

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🐳 Building Pill Detection API Container                 ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Configuration:${NC}"
echo "  Image Name:    ${FULL_IMAGE}"
echo "  Version:       ${VERSION}"
echo "  Build Date:    ${BUILD_DATE}"
echo "  Git Commit:    ${GIT_COMMIT}"
echo "  Platform:      linux/amd64"
echo ""

# Check if models directory exists
if [ ! -d "models" ] || [ ! -f "models/best.pt" ]; then
    echo -e "${RED}❌ Error: models/best.pt not found!${NC}"
    echo "   Please ensure your trained model is in ./models/best.pt"
    exit 1
fi

echo -e "${YELLOW}📦 Building Docker image...${NC}"
echo ""

# Build with multiple tags
docker build \
    -f Dockerfile.production \
    -t "${FULL_IMAGE}:${VERSION}" \
    -t "${FULL_IMAGE}:latest" \
    --build-arg BUILD_DATE="${BUILD_DATE}" \
    --build-arg VERSION="${VERSION}" \
    --build-arg GIT_COMMIT="${GIT_COMMIT}" \
    --platform linux/amd64 \
    .

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ Build Successful!                                     ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}Tagged images:${NC}"
    echo "  📦 ${FULL_IMAGE}:${VERSION}"
    echo "  📦 ${FULL_IMAGE}:latest"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "  1. Test locally:  ./run.sh"
    echo "  2. Push to registry:  ./push.sh"
    echo ""
else
    echo ""
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi
