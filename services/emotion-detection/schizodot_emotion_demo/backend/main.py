
from fastapi import FastAPI
from backend.services.emotion.api import router as emotion_router

app = FastAPI(title="SchizoDOT Emotion Backend")

@app.get("/health")
async def health():
    """Health check endpoint for Docker and monitoring"""
    return {
        "status": "healthy",
        "service": "emotion-detection",
        "version": "2.0.0"
    }

app.include_router(emotion_router, prefix="/v1")
