#!/bin/bash
# ============================================
# Full Stack Test Script - SchizoDot AI
# ============================================
# Tests complete Docker infrastructure

set -e

echo "================================================"
echo "SchizoDot AI - Full Stack Test"
echo "================================================"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check Docker
echo "1. Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Check .env file
echo "2. Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ .env file not found${NC}"
    echo "Creating from .env.example..."
    cp .env.example .env
    echo -e "${YELLOW}⚠ Please edit .env with your AWS credentials${NC}"
    echo "Then run this script again."
    exit 1
fi
echo -e "${GREEN}✓ .env file exists${NC}"
echo ""

# Build all images
echo "3. Building all Docker images..."
echo "This may take 10-15 minutes on first build..."
echo ""

if docker-compose build; then
    echo -e "${GREEN}✓ All images built successfully${NC}"
else
    echo -e "${RED}✗ Image build failed${NC}"
    exit 1
fi
echo ""

# Start services
echo "4. Starting all services..."
if docker-compose up -d; then
    echo -e "${GREEN}✓ All services started${NC}"
else
    echo -e "${RED}✗ Failed to start services${NC}"
    exit 1
fi
echo ""

# Wait for services to be ready
echo "5. Waiting for services to be healthy..."
echo "This may take 30-60 seconds..."
sleep 10

MAX_WAIT=60
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    HEALTHY=$(docker-compose ps | grep -c "(healthy)" || true)
    TOTAL=$(docker-compose ps | grep -c "Up" || true)
    
    echo -ne "\rHealthy services: $HEALTHY/$TOTAL"
    
    if [ "$HEALTHY" -ge 3 ]; then
        echo ""
        echo -e "${GREEN}✓ Services are healthy${NC}"
        break
    fi
    
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo ""
    echo -e "${YELLOW}⚠ Some services may not be fully healthy yet${NC}"
    echo "Continuing with tests..."
fi
echo ""

# Check service status
echo "6. Checking service status..."
docker-compose ps
echo ""

# Test Nginx health
echo "7. Testing Nginx health..."
if curl -f -s http://localhost/health > /dev/null; then
    echo -e "${GREEN}✓ Nginx is responding${NC}"
else
    echo -e "${RED}✗ Nginx health check failed${NC}"
fi
echo ""

# Test FastAPI health (via Nginx)
echo "8. Testing FastAPI health (via Nginx)..."
RESPONSE=$(curl -s http://localhost/api/v1/health)
if echo "$RESPONSE" | grep -q "ok"; then
    echo -e "${GREEN}✓ FastAPI is responding${NC}"
    echo "Response: $RESPONSE"
else
    echo -e "${RED}✗ FastAPI health check failed${NC}"
    echo "Response: $RESPONSE"
fi
echo ""

# Test FastAPI direct
echo "9. Testing FastAPI direct connection..."
RESPONSE=$(curl -s http://localhost:8000/api/v1/health)
if echo "$RESPONSE" | grep -q "ok"; then
    echo -e "${GREEN}✓ FastAPI direct access works${NC}"
else
    echo -e "${YELLOW}⚠ FastAPI direct access failed (may be expected)${NC}"
fi
echo ""

# Test AI Pipeline
echo "10. Testing AI Pipeline health..."
RESPONSE=$(curl -s http://localhost:8001/health || echo "failed")
if echo "$RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✓ AI Pipeline is responding${NC}"
    echo "Response: $RESPONSE"
else
    echo -e "${YELLOW}⚠ AI Pipeline not ready yet${NC}"
    echo "Response: $RESPONSE"
fi
echo ""

# Test Redis
echo "11. Testing Redis connection..."
if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
    echo -e "${GREEN}✓ Redis is responding${NC}"
else
    echo -e "${RED}✗ Redis connection failed${NC}"
fi
echo ""

# Test Celery Worker
echo "12. Testing Celery Worker..."
WORKER_STATUS=$(docker-compose exec -T celery-worker celery -A app.worker.celery_app inspect ping 2>&1 || echo "failed")
if echo "$WORKER_STATUS" | grep -q "pong"; then
    echo -e "${GREEN}✓ Celery worker is responding${NC}"
else
    echo -e "${YELLOW}⚠ Celery worker not ready yet${NC}"
    echo "This is normal on first startup"
fi
echo ""

# Check logs for errors
echo "13. Checking for errors in logs..."
ERRORS=$(docker-compose logs --tail=50 2>&1 | grep -i "error" | grep -v "error_log" || true)
if [ -z "$ERRORS" ]; then
    echo -e "${GREEN}✓ No errors found in recent logs${NC}"
else
    echo -e "${YELLOW}⚠ Some errors found (may be normal):${NC}"
    echo "$ERRORS" | head -5
fi
echo ""

# Test API documentation
echo "14. Testing API documentation..."
if curl -f -s http://localhost/docs > /dev/null; then
    echo -e "${GREEN}✓ API documentation accessible${NC}"
    echo "Visit: http://localhost/docs"
else
    echo -e "${YELLOW}⚠ API documentation not accessible${NC}"
fi
echo ""

# Summary
echo "================================================"
echo -e "${BLUE}Test Summary${NC}"
echo "================================================"
echo ""

# Count healthy services
HEALTHY_COUNT=$(docker-compose ps | grep -c "(healthy)" || echo "0")
RUNNING_COUNT=$(docker-compose ps | grep -c "Up" || echo "0")

echo "Services running: $RUNNING_COUNT"
echo "Services healthy: $HEALTHY_COUNT"
echo ""

if [ "$HEALTHY_COUNT" -ge 3 ]; then
    echo -e "${GREEN}✓ Stack is operational!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. View logs: docker-compose logs -f"
    echo "2. Test upload: Use frontend/index.html"
    echo "3. Monitor Celery: http://localhost:5555 (Flower)"
    echo "4. API docs: http://localhost/docs"
else
    echo -e "${YELLOW}⚠ Some services need more time to start${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check logs: docker-compose logs -f"
    echo "2. Check status: docker-compose ps"
    echo "3. Restart services: docker-compose restart"
fi

echo ""
echo "================================================"
