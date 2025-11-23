# backend/services/emotion/api.py
#
# FastAPI router for emotion prediction.
# Uses MultimodalEmotionModel (audio + face + fused).

import os
import tempfile

from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.services.emotion.multimodal_infer import MultimodalEmotionModel

router = APIRouter()

# Create one global multimodal model instance
model = MultimodalEmotionModel()


@router.post("/emotion/predict")
async def predict_emotion(file: UploadFile = File(...)):
    """
    Accept a video (mp4) or audio (wav), save it to a temp file,
    then run the multimodal model and return:
      {
        "audio": {...},
        "face": {...},
        "fused": {...}
      }
    """

    filename = (file.filename or "").lower()
    if not (filename.endswith(".mp4") or filename.endswith(".wav")):
        raise HTTPException(
            status_code=400,
            detail="Please upload a .mp4 video or .wav audio file.",
        )

    # 1. Save upload to a temporary file on disk
    suffix = os.path.splitext(filename)[1] or ".mp4"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        data = await file.read()
        tmp.write(data)
        tmp.flush()
        tmp_path = tmp.name
        tmp.close()

        # 2. Run multimodal model on that temp path
        out = model.predict_from_video(tmp_path)

        # 3. Return the multimodal result
        return out

    finally:
        # 4. Clean up temp file
        try:
            os.remove(tmp.name)
        except OSError:
            pass
