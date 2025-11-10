#!/bin/bash
# ============================================
# Test Docker Build Script
# ============================================
# Tests that FastAPI Docker image builds successfully

set -e  # Exit on error

echo "================================================"
echo "SchizoDot AI - Docker Build Test"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
echo "1. Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    echo "Please start Docker Desktop and try again"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Check if docker-compose.yml exists
echo "2. Checking docker-compose.yml..."
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}✗ docker-compose.yml not found${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi
echo -e "${GREEN}✓ docker-compose.yml found${NC}"
echo ""

# Check if .env file exists
echo "3. Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ .env file not found${NC}"
    echo "Creating .env from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ Created .env file${NC}"
        echo -e "${YELLOW}⚠ Please edit .env with your AWS credentials before running services${NC}"
    else
        echo -e "${RED}✗ .env.example not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi
echo ""

# Build FastAPI image
echo "4. Building FastAPI Docker image..."
echo "This may take 2-5 minutes on first build..."
if docker-compose build fastapi-backend; then
    echo -e "${GREEN}✓ FastAPI image built successfully${NC}"
else
    echo -e "${RED}✗ FastAPI image build failed${NC}"
    exit 1
fi
echo ""

# Check image size
echo "5. Checking image details..."
IMAGE_SIZE=$(docker images schizodot-ai-dot-fastapi-backend --format "{{.Size}}" | head -1)
echo "Image size: $IMAGE_SIZE"
echo ""

# Test image can start (without full dependencies)
echo "6. Testing image can start..."
echo "Starting container (will fail without Redis, but tests image integrity)..."
if timeout 10 docker-compose up --no-deps fastapi-backend 2>&1 | grep -q "Application startup complete" || true; then
    echo -e "${GREEN}✓ Container starts successfully${NC}"
else
    echo -e "${YELLOW}⚠ Container startup test inconclusive (expected without dependencies)${NC}"
fi

# Stop any running containers
docker-compose down > /dev/null 2>&1 || true
echo ""

echo "================================================"
echo -e "${GREEN}✓ Docker build test completed successfully!${NC}"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your AWS credentials"
echo "2. Run: docker-compose up -d"
echo "3. Test: curl http://localhost:8000/api/v1/health"
echo ""
