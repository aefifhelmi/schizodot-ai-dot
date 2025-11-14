# backend/services/emotion/api.py

import os
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.services.emotion.multimodal_infer import MultimodalEmotionModel

router = APIRouter()

model = MultimodalEmotionModel()

@router.post("/emotion/predict")
async def predict_emotion(file: UploadFile = File(...)):
    filename = file.filename.lower()
    if not filename.endswith(".mp4"):
        raise HTTPException(status_code=400, detail="Please upload an .mp4 video file.")

    tmp = NamedTemporaryFile(suffix=".mp4", delete=False)
    try:
        tmp.write(await file.read())
        tmp.flush()
        tmp_path = tmp.name
        tmp.close()

        out = model.predict_from_video(tmp_path)
        return out
    finally:
        try:
            os.remove(tmp.name)
        except OSError:
            pass
