#!/bin/bash
# Test multimodal emotion recognition with proper environment

cd "$(dirname "$0")"

echo "🎭 Testing Multimodal Emotion Recognition"
echo "=========================================="

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found"
    echo "Please run: python3 -m venv venv"
    exit 1
fi

# Activate venv
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import torch" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r backend/services/emotion/requirements.txt
fi

# Run test
export PYTHONPATH=$(pwd)
python scripts/test_multimodal.py
