# backend/services/emotion/audio_infer.py
from pathlib import Path
import numpy as np
import librosa
import joblib


class AudioEmotionModel:
    """Simple wrapper to load and use the trained RandomForest model."""

    def __init__(
        self,
        model_path: str = "ai/emotion/weights/audio_emotion_rf.joblib",
        label_path: str = "ai/emotion/weights/audio_emotion_labels.joblib",
        sample_rate: int = 16000,
        n_mfcc: int = 20,
    ):
        # find repo root (3 folders up from this file)
        root = Path(__file__).resolve().parents[3]
        self.model_path = root / model_path
        self.label_path = root / label_path
        self.sample_rate = sample_rate
        self.n_mfcc = n_mfcc

        if not self.model_path.exists():
            raise FileNotFoundError(f"Missing model: {self.model_path}")
        if not self.label_path.exists():
            raise FileNotFoundError(f"Missing labels: {self.label_path}")

        self.model = joblib.load(self.model_path)
        self.label_encoder = joblib.load(self.label_path)

    def _extract_mfcc(self, wav_path: str) -> np.ndarray:
        """Compute MFCCs averaged over time."""
        y, sr = librosa.load(wav_path, sr=self.sample_rate)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=self.n_mfcc)
        return mfcc.mean(axis=1).reshape(1, -1)

    def predict_from_path(self, wav_path: str) -> dict:
        """Return predicted emotion label and probabilities."""
        X = self._extract_mfcc(wav_path)
        probs = self.model.predict_proba(X)[0]
        idx = int(np.argmax(probs))
        label = self.label_encoder.inverse_transform([idx])[0]

        # cast to plain Python types
        label = str(label)
        probs_dict = {str(emo): float(p) for emo, p in zip(self.label_encoder.classes_, probs)}

        return {
            "label": label,
            "probs": probs_dict,
        }
