import os
import joblib
import numpy as np
import librosa

class AudioEmotionModel:
    def __init__(self, model_path: str | None = None, sample_rate: int = 22050):
        if model_path is None:
            # relative to backend/services/emotion/
            model_path = os.path.join(
                os.path.dirname(__file__),
                "..", "..", "..",
                "ai", "emotion", "weights", "audio_model.pkl",
            )
            model_path = os.path.normpath(model_path)

        obj = joblib.load(model_path)
        self.model = obj["model"]
        self.label_encoder = obj["label_encoder"]
        self.sample_rate = sample_rate
