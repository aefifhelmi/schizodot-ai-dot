
from fastapi import APIRouter, UploadFile, File, HTTPException
from .infer import AVEmotion
import numpy as np
import tempfile, os
import cv2
import soundfile as sf
import subprocess

router = APIRouter()
model = AVEmotion("ai/emotion/weights/av_emotion_best.pt")

def _extract_audio_wav(in_path: str, out_path: str, target_sr: int = 16000):
    cmd = [
        "ffmpeg", "-y",
        "-i", in_path,
        "-vn",
        "-ac", "1",
        "-ar", str(target_sr),
        out_path
    ]
    # Require ffmpeg in the container/host
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def _extract_face_frames(in_path: str, stride: int = 2, max_frames: int = 64):
    cap = cv2.VideoCapture(in_path)
    frames = []
    i = 0
    if not cap.isOpened():
        return frames
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if i % stride == 0:
            # BGR->RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame)
            if len(frames) >= max_frames:
                break
        i += 1
    cap.release()
    return frames

@router.post("/emotion/predict")
async def predict(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".mp4", ".mov", ".mkv", ".avi")):
        raise HTTPException(status_code=400, detail="Upload a video file")
    with tempfile.TemporaryDirectory() as td:
        in_path = os.path.join(td, file.filename)
        with open(in_path, "wb") as f:
            f.write(await file.read())

        # Extract audio
        wav_path = os.path.join(td, "audio.wav")
        try:
            _extract_audio_wav(in_path, wav_path, target_sr=16000)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"ffmpeg error: {e}")

        # Read audio
        audio, sr = sf.read(wav_path, dtype='float32', always_2d=False)
        if audio.ndim > 1:
            audio = audio[:, 0]

        # Extract simple RGB frames (face crops recommended in production)
        frames = _extract_face_frames(in_path)

        # Call model
        try:
            out = model.predict(frames, audio, sr)
        except NotImplementedError as e:
            raise HTTPException(status_code=501, detail=str(e))
        return out
