# backend/services/emotion/multimodal_infer.py
#
# MultimodalEmotionModel:
# - runs audio + face emotion models on the same video
# - returns audio result, face result, and a fused result.

from typing import Dict, Any

from backend.services.emotion.audio_infer import AudioEmotionModel
from backend.services.emotion.face_infer import FaceEmotionModel


class MultimodalEmotionModel:
    def __init__(self) -> None:
        self.audio_model = AudioEmotionModel()
        try:
            self.face_model = FaceEmotionModel(use_mtcnn=False)
        except ImportError:
            print("⚠️  FER not available, face detection disabled")
            self.face_model = None

        # map FER labels to audio space where names differ
        self.face_to_audio_label_map = {
            "fear": "fearful",
            "surprise": "surprised",
        }

    def _map_face_probs(self, face_probs: Dict[str, float]) -> Dict[str, float]:
        """
        Map FER label names to align with audio labels when needed.
        """
        mapped: Dict[str, float] = {}
        for k, v in face_probs.items():
            mapped_label = self.face_to_audio_label_map.get(k, k)
            mapped[mapped_label] = float(v)
        return mapped

    def predict_from_video(self, video_path: str) -> Dict[str, Any]:
        """
        Run both audio + face emotion models on the same video_path.
        Returns:
        {
          "audio": {...},
          "face": {...},
          "fused": {"label": "...", "probs": {...}}
        }
        """
        audio_out = self.audio_model.predict_from_video(video_path)
        
        if self.face_model:
            face_out = self.face_model.predict_from_video(video_path, step=5)
            face_probs_raw = face_out.get("probs", {}) or {}
            face_probs = self._map_face_probs(face_probs_raw)
        else:
            face_out = {"label": "neutral", "probs": {}, "frame_count": 0}
            face_probs = {}

        audio_probs = audio_out.get("probs", {}) or {}

        fused_probs: Dict[str, float] = {}

        # simple late fusion: average where both have values
        for emo in audio_probs.keys():
            a = float(audio_probs.get(emo, 0.0))
            f = float(face_probs.get(emo, 0.0))
            if emo in face_probs:
                fused_probs[emo] = 0.5 * a + 0.5 * f
            else:
                fused_probs[emo] = a

        fused_label = max(fused_probs, key=fused_probs.get) if fused_probs else None

        return {
            "audio": audio_out,
            "face": face_out,
            "fused": {
                "label": fused_label,
                "probs": fused_probs,
            },
        }
