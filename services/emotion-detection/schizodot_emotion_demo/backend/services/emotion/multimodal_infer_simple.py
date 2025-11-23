# backend/services/emotion/multimodal_infer.py
"""
Simplified multimodal emotion recognition matching developer's implementation
"""

from backend.services.emotion.audio_infer import AudioEmotionModel
from backend.services.emotion.face_infer import FaceEmotionModel
from typing import Dict, Any


class MultimodalEmotionModel:
    """
    Multimodal emotion recognition using audio + face models
    Matches developer's simple and clean implementation
    """
    
    def __init__(self):
        print("Loading multimodal emotion model...")
        self.audio_model = AudioEmotionModel()
        self.face_model = FaceEmotionModel()
        print("✅ Multimodal model loaded (audio + face)")
    
    def predict_from_video(self, video_path: str) -> Dict[str, Any]:
        """
        Run audio + face models on the same video and produce:
          - audio result
          - face result
          - simple fused label (average probs)
        """
        # Get predictions from both models
        audio_out = self.audio_model.predict_from_video(video_path)
        face_out = self.face_model.predict_from_video(video_path, step=5)
        
        # Fuse by averaging probabilities over shared emotion keys
        audio_probs = audio_out["probs"]
        face_probs = face_out["probs"]
        
        fused_probs = {}
        for emo in audio_probs.keys():
            if emo in face_probs:
                fused_probs[emo] = 0.5 * audio_probs[emo] + 0.5 * face_probs[emo]
            else:
                fused_probs[emo] = audio_probs[emo]
        
        fused_label = max(fused_probs, key=fused_probs.get)
        fused_confidence = fused_probs[fused_label]
        
        # Format response to match API expectations
        return {
            "audio": {
                "label": audio_out["label"],
                "probs": audio_out["probs"],
                "confidence": audio_out["probs"][audio_out["label"]]
            },
            "face": {
                "label": face_out["label"],
                "probs": face_out["probs"],
                "confidence": face_out["probs"][face_out["label"]]
            },
            "multimodal": {
                "label": fused_label,
                "probs": fused_probs,
                "confidence": fused_confidence
            },
            "model_type": "simple_fusion"
        }
