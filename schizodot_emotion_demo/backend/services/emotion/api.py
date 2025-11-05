# backend/services/emotion/api.py

import os
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.services.emotion.audio_infer import AudioEmotionModel
from backend.services.emotion.face_infer import FaceEmotionModel

router = APIRouter()

audio_model = AudioEmotionModel()
face_model = FaceEmotionModel()


@router.post("/emotion/predict")
async def predict_emotion(file: UploadFile = File(...)):
    """
    Accept one .mp4 video file and return:
      - audio-based emotion
      - face-based emotion
    """
    filename = file.filename.lower()
    if not filename.endswith(".mp4"):
        raise HTTPException(status_code=400, detail="Please upload an .mp4 video file.")

    # On Windows, NamedTemporaryFile must use delete=False to avoid locking
    tmp = NamedTemporaryFile(suffix=".mp4", delete=False)
    try:
        # write upload, then close so other libs can read it
        tmp.write(await file.read())
        tmp.flush()
        tmp_path = tmp.name
        tmp.close()

        # run both models on the same file path
        audio_out = audio_model.predict_from_path(tmp_path)
        face_out = face_model.predict_from_video(tmp_path, step=5)

        return {"audio": audio_out, "face": face_out}
    finally:
        try:
            os.remove(tmp.name)
        except OSError:
            pass
