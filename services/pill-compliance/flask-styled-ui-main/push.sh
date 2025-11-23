#!/bin/bash
# ============================================
# Push Script - Pill Detection API
# ============================================
# Push to container registry with version tags

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration - Set these via environment or modify defaults
IMAGE_NAME="${IMAGE_NAME:-pill-detection-api}"
REGISTRY="${REGISTRY:-}"  # e.g., "docker.io/yourname/" or "gcr.io/project-id/"
VERSION="${VERSION:-1.0.0}"

if [ -z "$REGISTRY" ]; then
    echo -e "${RED}❌ Error: REGISTRY not set!${NC}"
    echo ""
    echo "Set the registry URL:"
    echo "  export REGISTRY='docker.io/yourname/'"
    echo "  export REGISTRY='gcr.io/project-id/'"
    echo "  export REGISTRY='yourregistry.azurecr.io/'"
    echo ""
    echo "Then run: ./push.sh"
    exit 1
fi

FULL_IMAGE="${REGISTRY}${IMAGE_NAME}"

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  📤 Pushing to Container Registry                         ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Configuration:${NC}"
echo "  Registry:  ${REGISTRY}"
echo "  Image:     ${IMAGE_NAME}"
echo "  Version:   ${VERSION}"
echo ""

# Check if local image exists
if ! docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "${IMAGE_NAME}:${VERSION}"; then
    echo -e "${RED}❌ Error: Image ${IMAGE_NAME}:${VERSION} not found locally!${NC}"
    echo "   Run ./build.sh first"
    exit 1
fi

# Tag for registry
echo -e "${YELLOW}🏷️  Tagging images...${NC}"
docker tag "${IMAGE_NAME}:${VERSION}" "${FULL_IMAGE}:${VERSION}"
docker tag "${IMAGE_NAME}:${VERSION}" "${FULL_IMAGE}:latest"

# Push images
echo ""
echo -e "${YELLOW}📤 Pushing ${FULL_IMAGE}:${VERSION}...${NC}"
docker push "${FULL_IMAGE}:${VERSION}"

echo ""
echo -e "${YELLOW}📤 Pushing ${FULL_IMAGE}:latest...${NC}"
docker push "${FULL_IMAGE}:latest"

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ Push Successful!                                      ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Images pushed:${NC}"
echo "  📦 ${FULL_IMAGE}:${VERSION}"
echo "  📦 ${FULL_IMAGE}:latest"
echo ""
echo -e "${BLUE}Deploy in production:${NC}"
echo "  docker run -d -p 8003:8003 ${FULL_IMAGE}:${VERSION}"
echo ""
echo -e "${BLUE}Or use docker-compose-production.yml${NC}"
echo ""
