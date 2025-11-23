# backend/services/emotion/audio_infer.py
#
# AudioEmotionModel:
# - loads pretrained RandomForest + LabelEncoder from:
#     ai/emotion/weights/audio_model.pkl
#     ai/emotion/weights/audio_label_encoder.pkl
# - can take either a WAV file or a video file (MP4),
#   for video it extracts audio to a temp WAV using ffmpeg.

import os
import subprocess
import tempfile
from typing import Dict, Any

import numpy as np
import librosa
import joblib


class AudioEmotionModel:
    def __init__(self, sample_rate: int = 16000, n_mfcc: int = 40) -> None:
        base_dir = os.path.dirname(__file__)  # .../backend/services/emotion
        repo_root = os.path.normpath(os.path.join(base_dir, "..", "..", ".."))
        weights_dir = os.path.join(repo_root, "ai", "emotion", "weights")

        model_path = os.path.join(weights_dir, "audio_model.pkl")
        le_path = os.path.join(weights_dir, "audio_label_encoder.pkl")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Audio model not found at {model_path}")
        if not os.path.exists(le_path):
            raise FileNotFoundError(f"Label encoder not found at {le_path}")

        self.model = joblib.load(model_path)
        self.label_encoder = joblib.load(le_path)
        self.sample_rate = sample_rate
        self.n_mfcc = n_mfcc

    # ---------- internal helpers ----------

    def _extract_mfcc(self, wav_path: str) -> np.ndarray:
        y, sr = librosa.load(wav_path, sr=self.sample_rate)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=self.n_mfcc)
        feats = np.mean(mfcc.T, axis=0)
        return feats.reshape(1, -1)  # (1, n_features)

    def _ensure_wav(self, path: str) -> str:
        """
        If path is a WAV, just return it.
        If it is a video (mp4, mov, mkv), extract mono WAV with ffmpeg.
        """
        ext = os.path.splitext(path)[1].lower()

        if ext in [".wav"]:
            return path

        # assume it's a video file – extract audio
        tmp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp_wav.close()
        cmd = [
            "ffmpeg",
            "-y",
            "-i", path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", str(self.sample_rate),
            "-ac", "1",
            tmp_wav.name,
        ]
        # run ffmpeg quietly
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return tmp_wav.name

    # ---------- public API ----------

    def predict_from_path(self, path: str) -> Dict[str, Any]:
        """
        Path can be a WAV or a video file.
        Returns: {"label": str, "probs": {emotion: prob, ...}}
        """
        tmp_to_delete = None
        try:
            wav_path = path
            ext = os.path.splitext(path)[1].lower()
            if ext not in [".wav"]:
                wav_path = self._ensure_wav(path)
                tmp_to_delete = wav_path

            X = self._extract_mfcc(wav_path)
            probs = self.model.predict_proba(X)[0]
            idx = int(np.argmax(probs))
            label = self.label_encoder.inverse_transform([idx])[0]

            classes = self.label_encoder.classes_
            probs_dict = {
                str(emotion): float(p) for emotion, p in zip(classes, probs)
            }

            return {
                "label": str(label),
                "probs": probs_dict,
            }

        finally:
            if tmp_to_delete and os.path.exists(tmp_to_delete):
                try:
                    os.remove(tmp_to_delete)
                except OSError:
                    pass

    def predict_from_video(self, video_path: str) -> Dict[str, Any]:
        """
        Alias for predict_from_path, for compatibility.
        """
        return self.predict_from_path(video_path)
