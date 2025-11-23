#!/usr/bin/env python3
"""
Start the emotion service with proper environment setup
"""
import os
import sys

# Set matplotlib to non-interactive backend BEFORE any imports
os.environ['MPLBACKEND'] = 'Agg'

# Disable TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Set OpenCV to headless mode
os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

# Now import and run uvicorn
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8003,
        log_level="info"
    )
