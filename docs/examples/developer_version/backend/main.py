
from fastapi import FastAPI
from backend.services.emotion.api import router as emotion_router

app = FastAPI(title="SchizoDOT Emotion Backend")
app.include_router(emotion_router, prefix="/v1")
