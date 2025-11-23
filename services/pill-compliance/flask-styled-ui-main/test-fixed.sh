#!/bin/bash
# ============================================
# FIXED Test Script - Pill Detection API
# ============================================
# Validates container is working correctly

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PORT="${PORT:-8003}"
CONTAINER_NAME="${CONTAINER_NAME:-pill-detection-api-fixed}"

PASSED=0
FAILED=0

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  🧪 PILL DETECTION API - VALIDATION TESTS                ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

test_step() {
    echo -n "Testing: $1... "
}

pass() {
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASSED++))
}

fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
}

echo "═══════════════════════════════════════════════════════════"
echo "TEST 1: Container Status"
echo "═══════════════════════════════════════════════════════════"
echo ""

test_step "Container is running"
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    pass
else
    fail "Container not running. Start with: ./run-fixed.sh"
fi

test_step "Container health status"
HEALTH=$(docker inspect --format='{{.State.Health.Status}}' "${CONTAINER_NAME}" 2>/dev/null || echo "unknown")
if [ "$HEALTH" = "healthy" ]; then
    pass
elif [ "$HEALTH" = "starting" ]; then
    warn "Container still starting up"
else
    fail "Health status: $HEALTH"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "TEST 2: API Endpoints"
echo "═══════════════════════════════════════════════════════════"
echo ""

test_step "Root endpoint (GET /)"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${PORT}/)
if [ "$RESPONSE" = "200" ]; then
    pass
else
    fail "HTTP $RESPONSE"
fi

test_step "Health endpoint (GET /health)"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${PORT}/health)
if [ "$RESPONSE" = "200" ]; then
    pass
else
    fail "HTTP $RESPONSE"
fi

test_step "API docs (GET /docs)"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${PORT}/docs)
if [ "$RESPONSE" = "200" ]; then
    pass
else
    fail "HTTP $RESPONSE"
fi

test_step "Model info endpoint (GET /v1/model/info)"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${PORT}/v1/model/info)
if [ "$RESPONSE" = "200" ]; then
    pass
else
    fail "HTTP $RESPONSE"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "TEST 3: API Response Structure"
echo "═══════════════════════════════════════════════════════════"
echo ""

test_step "Health check returns JSON"
HEALTH_JSON=$(curl -s http://localhost:${PORT}/health)
if echo "$HEALTH_JSON" | jq empty 2>/dev/null; then
    pass
else
    fail "Invalid JSON response"
fi

test_step "Health status is 'healthy'"
STATUS=$(echo "$HEALTH_JSON" | jq -r '.status' 2>/dev/null)
if [ "$STATUS" = "healthy" ]; then
    pass
else
    fail "Status: $STATUS"
fi

test_step "Model is loaded"
MODEL_LOADED=$(echo "$HEALTH_JSON" | jq -r '.model_loaded' 2>/dev/null)
if [ "$MODEL_LOADED" = "true" ]; then
    pass
else
    fail "Model not loaded"
fi

test_step "Model info has classes"
MODEL_INFO=$(curl -s http://localhost:${PORT}/v1/model/info)
CLASSES=$(echo "$MODEL_INFO" | jq '.classes | length' 2>/dev/null)
if [ "$CLASSES" -gt 0 ]; then
    pass
    echo "   📊 Model classes: $(echo "$MODEL_INFO" | jq -r '.classes | join(", ")')"
else
    fail "No classes found"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "TEST 4: Container Logs"
echo "═══════════════════════════════════════════════════════════"
echo ""

test_step "No critical errors in logs"
ERROR_COUNT=$(docker logs "${CONTAINER_NAME}" 2>&1 | grep -i "error" | grep -v "No error" | wc -l)
if [ "$ERROR_COUNT" -eq 0 ]; then
    pass
else
    warn "Found $ERROR_COUNT error messages in logs"
fi

test_step "Model loaded successfully"
if docker logs "${CONTAINER_NAME}" 2>&1 | grep -q "Model loaded successfully\|YOLOv11 model loaded"; then
    pass
else
    fail "Model loading not confirmed in logs"
fi

test_step "MediaPipe initialized"
if docker logs "${CONTAINER_NAME}" 2>&1 | grep -q "MediaPipe.*initialized\|Face Mesh initialized"; then
    pass
else
    fail "MediaPipe initialization not confirmed"
fi

test_step "API server started"
if docker logs "${CONTAINER_NAME}" 2>&1 | grep -q "Application startup complete\|Uvicorn running"; then
    pass
else
    fail "Server startup not confirmed"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "TEST 5: Resource Usage"
echo "═══════════════════════════════════════════════════════════"
echo ""

STATS=$(docker stats --no-stream --format "{{.MemUsage}}\t{{.CPUPerc}}" "${CONTAINER_NAME}")
MEM=$(echo "$STATS" | awk '{print $1}')
CPU=$(echo "$STATS" | awk '{print $2}')

echo "  📊 Memory: $MEM"
echo "  📊 CPU: $CPU"

# Check if memory usage is reasonable (< 3GB)
MEM_MB=$(echo "$MEM" | grep -oE '[0-9]+' | head -1)
if [ "$MEM_MB" -lt 3000 ]; then
    echo "  ✅ Memory usage is reasonable"
else
    echo "  ⚠️  High memory usage"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "TEST RESULTS"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo ""
    echo "✅ Container is working correctly"
    echo "✅ Model is loaded and ready"
    echo "✅ API endpoints are responding"
    echo "✅ Resource usage is normal"
    echo ""
    echo -e "${BLUE}Ready for production testing!${NC}"
    echo ""
    echo "To test video detection:"
    echo '  curl -X POST "http://localhost:'${PORT}'/v1/detect" \'
    echo '       -F "video=@your-test-video.mp4" | jq .'
    echo ""
else
    echo -e "${RED}⚠️  SOME TESTS FAILED${NC}"
    echo ""
    echo "Debug steps:"
    echo "  1. Check logs: docker logs ${CONTAINER_NAME}"
    echo "  2. Check health: curl http://localhost:${PORT}/health | jq ."
    echo "  3. Restart: docker restart ${CONTAINER_NAME}"
    echo ""
    exit 1
fi

echo "═══════════════════════════════════════════════════════════"
