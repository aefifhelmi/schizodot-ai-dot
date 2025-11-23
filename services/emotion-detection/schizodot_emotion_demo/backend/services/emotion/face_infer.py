# backend/services/emotion/face_infer.py

from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd
try:
    from fer.fer import FER
    from fer.classes import Video
    print("✅ FER loaded successfully")
except ImportError:
    try:
        from fer import FER
        from fer.classes import Video
        print("✅ FER loaded from fer module")
    except ImportError:
        FER = None
        Video = None
        print("⚠️ FER not available")


class FaceEmotionModel:
    """
    Wrapper around the FER library for video-based facial emotion recognition.
    Uses a pre-trained CNN model (no training needed).
    """

    def __init__(self, use_mtcnn: bool = False):
        # mtcnn=True is more accurate but a bit slower
        if FER is None:
            raise ImportError("FER library not available")
        self.detector = FER(mtcnn=use_mtcnn)

    def predict_from_video(self, video_path: str, step: int = 5) -> Dict[str, Any]:
        """
        Analyze a video and return:
          - overall dominant emotion label
          - average probabilities across frames
          - number of frames analyzed

        Parameters
        ----------
        video_path : str
            Path to an .mp4 video file.
        step : int
            Analyze every Nth frame (higher = faster, less precise).
        """
        video_path = str(Path(video_path))
        video = Video(video_path)

        # Analyze video, do not display
        raw_data = video.analyze(self.detector, display=False, frequency=step)
        df = video.to_pandas(raw_data)

        if df is None or len(df) == 0:
            return {"label": None, "probs": {}, "frame_count": 0}

        # FER uses these emotion names
        emotion_cols = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]
        # Keep only existing columns
        emotion_cols = [c for c in emotion_cols if c in df.columns]

        # Average probabilities across frames
        mean_probs = df[emotion_cols].mean().to_dict()

        # Pick dominant emotion
        top_label = max(mean_probs, key=mean_probs.get)

        # Cast to plain Python types
        mean_probs = {str(k): float(v) for k, v in mean_probs.items()}
        top_label = str(top_label)

        return {
            "label": top_label,
            "probs": mean_probs,
            "frame_count": int(len(df)),
        }
