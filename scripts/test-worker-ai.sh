#!/bin/bash
# ============================================
# Test Worker & AI Pipeline Docker Build
# ============================================

set -e

echo "================================================"
echo "SchizoDot AI - Worker & AI Pipeline Build Test"
echo "================================================"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check Docker
echo "1. Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Build Worker image
echo "2. Building Celery Worker image..."
if docker-compose build celery-worker; then
    echo -e "${GREEN}✓ Worker image built successfully${NC}"
else
    echo -e "${RED}✗ Worker image build failed${NC}"
    exit 1
fi
echo ""

# Build AI Pipeline image
echo "3. Building AI Pipeline image..."
echo "This may take 5-10 minutes (downloading PyTorch, etc.)..."
if docker-compose build ai-pipeline; then
    echo -e "${GREEN}✓ AI Pipeline image built successfully${NC}"
else
    echo -e "${RED}✗ AI Pipeline image build failed${NC}"
    exit 1
fi
echo ""

# Check image sizes
echo "4. Checking image details..."
echo "Worker image:"
docker images | grep "schizodot.*worker" | head -1
echo "AI Pipeline image:"
docker images | grep "schizodot.*ai-pipeline" | head -1
echo ""

echo "================================================"
echo -e "${GREEN}✓ All images built successfully!${NC}"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Start Redis: docker-compose up -d redis"
echo "2. Start Worker: docker-compose up -d celery-worker"
echo "3. Start AI Pipeline: docker-compose up -d ai-pipeline"
echo "4. Check logs: docker-compose logs -f celery-worker ai-pipeline"
echo ""
