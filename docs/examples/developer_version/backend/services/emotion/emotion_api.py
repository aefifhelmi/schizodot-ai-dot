# backend/services/emotion/emotion_api.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from tempfile import NamedTemporaryFile
from typing import Optional

from backend.services.emotion.emotion_service import EmotionService

router = APIRouter()
service = EmotionService()


@router.post("/emotion/analyze")
async def analyze_emotion(
    audio: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None),
):
    """
    Accepts:
      - audio: optional .wav file
      - video: optional .mp4 file

    Returns combined audio + face emotions.
    """
    if audio is None and video is None:
        raise HTTPException(status_code=400, detail="Provide at least audio or video")

    audio_path = None
    video_path = None

    if audio is not None:
        if not audio.filename.lower().endswith(".wav"):
            raise HTTPException(status_code=400, detail="Audio must be a .wav file")
        with NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(await audio.read())
            tmp.flush()
            audio_path = tmp.name

    if video is not None:
        if not video.filename.lower().endswith(".mp4"):
            raise HTTPException(status_code=400, detail="Video must be a .mp4 file")
        with NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(await video.read())
            tmp.flush()
            video_path = tmp.name

    out = service.analyze(audio_path=audio_path, video_path=video_path)
    return out
