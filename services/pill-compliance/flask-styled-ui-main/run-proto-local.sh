#!/bin/bash
# ============================================
# Run Proto LOCALLY (not in Docker)
# ============================================
# Use this for camera access on macOS

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🚀 Starting Real-Time Flask Proto (LOCAL)                ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if proto.py exists
if [ ! -f "proto.py" ]; then
    echo -e "${RED}❌ Error: proto.py not found!${NC}"
    exit 1
fi

# Check if model exists
if [ ! -f "models/best.pt" ]; then
    echo -e "${RED}❌ Error: models/best.pt not found!${NC}"
    exit 1
fi

echo -e "${GREEN}Starting local Flask application...${NC}"
echo "  Port: 5000"
echo "  Camera: Local (macOS camera access)"
echo ""

# Export environment variable for model loading
export TORCH_LOAD_WEIGHTS_ONLY=0

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: python3 not found!${NC}"
    exit 1
fi

echo -e "${YELLOW}📷 Opening Flask application...${NC}"
echo "   Browser will open to: http://localhost:5000/"
echo ""
echo -e "${BLUE}Press Ctrl+C to stop${NC}"
echo ""

# Run proto.py directly
python3 proto.py
