"""
FastAPI Service for Pill Detection
Provides REST API compatible with backend pipeline
"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import tempfile
import os
from pathlib import Path
import logging
from datetime import datetime

from simple_detector import SimplePillDetector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Pill Detection Service",
    description="Medication compliance detection using YOLOv11 + MediaPipe",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize detector
MODEL_PATH = os.getenv("MODEL_PATH", "./models/best.pt")
DEVICE = os.getenv("DEVICE", "cpu")

detector = None

@app.on_event("startup")
async def startup_event():
    """Initialize detector on startup"""
    global detector
    try:
        logger.info("=" * 60)
        logger.info("🚀 Starting Pill Detection Service")
        logger.info("=" * 60)
        logger.info(f"Model path: {MODEL_PATH}")
        logger.info(f"Device: {DEVICE}")
        
        detector = SimplePillDetector(model_path=MODEL_PATH)
        
        logger.info("=" * 60)
        logger.info("✅ Pill Detection Service Ready!")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"❌ Failed to initialize detector: {e}", exc_info=True)
        detector = None


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "pill-detection",
        "version": "1.0.0",
        "status": "healthy" if detector else "error",
        "endpoints": {
            "health": "/health",
            "detect": "/v1/detect"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if detector else "unhealthy",
        "service": "pill-detection",
        "model_loaded": detector is not None,
        "model_path": MODEL_PATH,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/v1/detect")
async def detect_compliance(video: UploadFile = File(...)):
    """
    Detect medication compliance in video
    
    Args:
        video: Video file (MP4, AVI, MOV, etc.)
        
    Returns:
        Compliance analysis results with score and detected objects
    """
    if detector is None:
        logger.error("Detector not initialized")
        raise HTTPException(
            status_code=503,
            detail="Detector not initialized. Check server logs."
        )
    
    # Validate file
    if not video.content_type or not video.content_type.startswith("video/"):
        logger.warning(f"Invalid content type: {video.content_type}")
        raise HTTPException(
            status_code=400,
            detail=f"File must be a video, got: {video.content_type}"
        )
    
    tmp_path = None
    
    try:
        # Save uploaded file temporarily
        suffix = Path(video.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await video.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        logger.info(f"📹 Processing video: {video.filename} ({len(content)} bytes)")
        
        # Run detection
        start_time = datetime.utcnow()
        results = detector.analyze_video(tmp_path, sample_rate=5)
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Add metadata
        results.update({
            "filename": video.filename,
            "file_size_bytes": len(content),
            "model": "yolov11_pill_detection",
            "device": DEVICE,
            "processing_time_ms": int(processing_time * 1000),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"✅ Detection complete: {results['verification_status']} "
                   f"(score: {results['compliance_score']:.2f}, "
                   f"time: {processing_time:.2f}s)")
        
        return JSONResponse(content=results)
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Detection failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Detection failed: {str(e)}"
        )
    
    finally:
        # Cleanup temp file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except:
                pass


@app.get("/v1/model/info")
async def model_info():
    """Get model information"""
    if detector is None:
        raise HTTPException(status_code=503, detail="Detector not initialized")
    
    return {
        "model_type": "YOLOv11",
        "framework": "Ultralytics",
        "classes": detector.classes,
        "thresholds": detector.thresholds,
        "model_path": MODEL_PATH
    }


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        log_level="info"
    )
