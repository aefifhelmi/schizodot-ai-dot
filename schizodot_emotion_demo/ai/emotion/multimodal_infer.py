# backend/services/emotion/multimodal_infer.py

from backend.services.emotion.audio_infer import AudioEmotionModel
from backend.services.emotion.face_infer import FaceEmotionModel

class MultimodalEmotionModel:
    def __init__(self):
        self.audio_model = AudioEmotionModel()
        self.face_model = FaceEmotionModel()

    def predict_from_video(self, video_path: str) -> dict:
        """
        Run audio + face models on the same video and produce:
          - audio result
          - face result
          - simple fused label (average probs)
        """
        audio_out = self.audio_model.predict_from_video(video_path)
        face_out = self.face_model.predict_from_video(video_path, step=5)

        # fuse by averaging probabilities over shared emotion keys
        audio_probs = audio_out["probs"]
        face_probs = face_out["probs"]

        fused_probs = {}
        for emo in audio_probs.keys():
            if emo in face_probs:
                fused_probs[emo] = 0.5 * audio_probs[emo] + 0.5 * face_probs[emo]
            else:
                fused_probs[emo] = audio_probs[emo]

        fused_label = max(fused_probs, key=fused_probs.get)

        return {
            "audio": audio_out,
            "face": face_out,
            "fused": {
                "label": fused_label,
                "probs": fused_probs,
            },
        }
