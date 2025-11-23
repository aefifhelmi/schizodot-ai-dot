# backend/services/emotion/emotion_service.py

from typing import Any, Dict, Optional

from backend.services.emotion.audio_infer import AudioEmotionModel
from backend.services.emotion.face_infer import FaceEmotionModel


class EmotionService:
    """
    High-level wrapper combining:
      - AudioEmotionModel (speech)
      - FaceEmotionModel  (video frames)
    """

    def __init__(self):
        self.audio_model = AudioEmotionModel()
        self.face_model = FaceEmotionModel()

    def analyze(
        self,
        audio_path: Optional[str] = None,
        video_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run audio and/or face analysis.

        Parameters
        ----------
        audio_path : str or None
            Path to a .wav file for speech emotion.
        video_path : str or None
            Path to a .mp4 file for facial emotion.

        Returns
        -------
        dict with keys:
          - audio (or None)
          - face  (or None)
        """
        result: Dict[str, Any] = {"audio": None, "face": None}

        if audio_path is not None:
            audio_out = self.audio_model.predict_from_path(audio_path)
            result["audio"] = audio_out

        if video_path is not None:
            face_out = self.face_model.predict_from_video(video_path, step=5)
            result["face"] = face_out

        return result
