
from pathlib import Path
import sys
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[3]
# Make the submodule importable
sys.path.append(str(ROOT / "external" / "emotion-av"))

# TODO: replace with actual imports from the upstream repo
# from model import FusionModel
# from datasets.transforms import build_video_tensor, build_audio_tensor

_EMO_LABELS = ["neutral","calm","happy","sad","angry","fearful","disgust","surprised"]

class AVEmotion:
    """Thin wrapper that exposes a stable .predict() API."
    """
    def __init__(self, ckpt_path: str):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.ckpt_path = ckpt_path

        # TODO: construct the model per upstream code
        # self.model = FusionModel(...)
        # state = torch.load(self.ckpt_path, map_location=self.device)
        # self.model.load_state_dict(state.get("state_dict", state))
        # self.model.eval().to(self.device)

    def _to_video_tensor(self, face_frames):
        """Convert a list of HxWx3 RGB numpy arrays into the expected video tensor.

        Replace with upstream transform utilities to ensure identical preprocessing.

        """
        # TODO: use upstream transforms. Placeholder below.
        raise NotImplementedError("Wire video preprocessing to upstream transforms.")

    def _to_audio_tensor(self, waveform: np.ndarray, sr: int):
        """Convert a 1D float32 waveform to the expected audio tensor.

        Replace with upstream transform utilities to ensure identical preprocessing.

        """
        # TODO: use upstream transforms. Placeholder below.
        raise NotImplementedError("Wire audio preprocessing to upstream transforms.")

    @torch.inference_mode()
    def predict(self, face_frames, audio_waveform: np.ndarray, sr: int):
        """Return {'label': str, 'probs': List[float]}.

        face_frames: list of RGB frames (HxWx3 np.uint8)

        audio_waveform: 1D float32 np.ndarray

        sr: sample rate

        """
        # x_v = self._to_video_tensor(face_frames).to(self.device)
        # x_a = self._to_audio_tensor(audio_waveform, sr).to(self.device)

        # logits = self.model(x_v, x_a)

        # probs = torch.softmax(logits, dim=-1).cpu().numpy()[0]

        # idx = int(np.argmax(probs))

        # return {'label': _EMO_LABELS[idx], 'probs': probs.tolist()}

        raise NotImplementedError("Complete predict() after wiring transforms and model.")
