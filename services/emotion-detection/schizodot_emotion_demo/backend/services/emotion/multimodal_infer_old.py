"""
Multimodal Emotion Recognition using pretrained audiovisual model
"""
import sys
import torch
import numpy as np
import cv2
import librosa
from pathlib import Path
from typing import Dict, Any

# Add external/emotion-av to path
REPO_ROOT = Path(__file__).resolve().parents[5]
emotion_av_path = REPO_ROOT / "external" / "emotion-av"
sys.path.insert(0, str(emotion_av_path))

try:
    from models import resnet, pre_act_resnet, wide_resnet, resnext, densenet
    from models.model import generate_model
except ImportError:
    print("⚠️  emotion-av models not found. Using stub mode.")
    generate_model = None


class MultimodalEmotionModel:
    """
    Wrapper for pretrained audiovisual emotion recognition model
    Falls back to FER + stub audio if pretrained model not available
    """
    
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.emotions = ['neutral', 'calm', 'happy', 'sad', 'angry', 'fearful', 'disgust', 'surprised']
        
        # Try to load pretrained model
        # Path: multimodal_infer.py -> emotion -> services -> backend -> schizodot_emotion_demo
        weights_path = Path(__file__).resolve().parents[3] / "ai/emotion/weights/av_emotion_best.pth"
        
        if weights_path.exists() and generate_model is not None:
            try:
                self.model = self._load_pretrained_model(weights_path)
                self.use_pretrained = True
                print(f"✅ Loaded pretrained multimodal model from {weights_path}")
            except Exception as e:
                print(f"⚠️  Failed to load pretrained model: {e}")
                print("   Using FER fallback mode")
                self.use_pretrained = False
                self._setup_fallback()
        else:
            print(f"⚠️  Pretrained model not found at {weights_path}")
            print("   Using FER fallback mode")
            self.use_pretrained = False
            self._setup_fallback()
    
    def _load_pretrained_model(self, weights_path: Path):
        """Load the pretrained audiovisual model"""
        # Create model with same architecture as training
        class Opts:
            model = 'resnet'
            model_depth = 18
            resnet_shortcut = 'A'
            wide_resnet_k = 2
            resnext_cardinality = 32
            sample_size = 112
            sample_duration = 16
            fusion = 'ia'  # intermediate attention
            n_classes = 8
            audio_model = 'resnet'
            audio_model_depth = 18
        
        opt = Opts()
        model = generate_model(opt)
        
        # Load weights
        checkpoint = torch.load(weights_path, map_location=self.device)
        
        # Handle different checkpoint formats
        if 'state_dict' in checkpoint:
            state_dict = checkpoint['state_dict']
        else:
            state_dict = checkpoint
        
        # Remove 'module.' prefix if present (from DataParallel)
        new_state_dict = {}
        for k, v in state_dict.items():
            name = k.replace('module.', '')
            new_state_dict[name] = v
        
        model.load_state_dict(new_state_dict)
        model.to(self.device)
        model.eval()
        
        return model
    
    def _setup_fallback(self):
        """Setup FER-based fallback"""
        try:
            from fer.fer import FER
            self.fer_detector = FER(mtcnn=True)
            print("✅ FER loaded successfully")
        except (ImportError, Exception) as e:
            print(f"⚠️  FER not available: {e}")
            print("   Using stub predictions")
            self.fer_detector = None
        
        # Setup audio emotion model
        try:
            from backend.services.emotion.audio_infer import AudioEmotionModel
            self.audio_model = AudioEmotionModel()
            print("✅ Audio emotion model loaded successfully")
        except Exception as e:
            print(f"⚠️  Audio model not available: {e}")
            print("   Using stub audio predictions")
            self.audio_model = None
    
    def predict_from_video(self, video_path: str) -> Dict[str, Any]:
        """
        Predict emotion from video file
        
        Returns:
            {
                "audio": {"label": str, "probs": dict, "confidence": float},
                "face": {"label": str, "probs": dict, "confidence": float},
                "multimodal": {"label": str, "probs": dict, "confidence": float},
                "model_type": str
            }
        """
        if self.use_pretrained:
            return self._predict_pretrained(video_path)
        else:
            return self._predict_fallback(video_path)
    
    def _predict_pretrained(self, video_path: str) -> Dict[str, Any]:
        """Use pretrained multimodal model"""
        try:
            # Extract video frames
            frames = self._extract_frames(video_path)
            
            # Extract audio
            audio = self._extract_audio(video_path)
            
            # Prepare inputs
            video_tensor = self._preprocess_video(frames)
            audio_tensor = self._preprocess_audio(audio)
            
            # Run inference
            with torch.no_grad():
                outputs = self.model(video_tensor, audio_tensor)
                probs = torch.nn.functional.softmax(outputs, dim=1)[0]
                probs_np = probs.cpu().numpy()
            
            # Get predictions
            pred_idx = int(np.argmax(probs_np))
            pred_label = self.emotions[pred_idx]
            confidence = float(probs_np[pred_idx])
            
            probs_dict = {
                emotion: float(prob) 
                for emotion, prob in zip(self.emotions, probs_np)
            }
            
            return {
                "audio": {"label": pred_label, "probs": probs_dict, "confidence": confidence},
                "face": {"label": pred_label, "probs": probs_dict, "confidence": confidence},
                "multimodal": {"label": pred_label, "probs": probs_dict, "confidence": confidence},
                "model_type": "pretrained_multimodal"
            }
            
        except Exception as e:
            print(f"⚠️  Pretrained model inference failed: {e}")
            return self._predict_fallback(video_path)
    
    def _predict_fallback(self, video_path: str) -> Dict[str, Any]:
        """Use FER + stub audio as fallback"""
        # Face emotion using FER
        if self.fer_detector:
            try:
                import cv2
                import pandas as pd
                
                # Open video and sample frames
                cap = cv2.VideoCapture(video_path)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                
                # Sample every 5th frame
                frame_indices = range(0, total_frames, 5)
                emotions_list = []
                
                for idx in frame_indices:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Detect emotions in frame
                    result = self.fer_detector.detect_emotions(frame)
                    if result and len(result) > 0:
                        # Get first face
                        emotions_list.append(result[0]['emotions'])
                
                cap.release()
                
                if emotions_list:
                    # Use weighted average that emphasizes stronger emotions
                    df = pd.DataFrame(emotions_list)
                    
                    # Calculate both mean and max for each emotion
                    mean_probs = df.mean().to_dict()
                    max_probs = df.max().to_dict()
                    
                    # Weighted combination: 60% max (captures peak emotions) + 40% mean (smooths noise)
                    # This helps detect strong emotions like angry/disgust even if they don't appear in all frames
                    weighted_probs = {
                        emotion: 0.6 * max_probs.get(emotion, 0.0) + 0.4 * mean_probs.get(emotion, 0.0)
                        for emotion in mean_probs.keys()
                    }
                    
                    # Map to our 8 emotions (add calm)
                    face_probs = {
                        "neutral": weighted_probs.get("neutral", 0.0),
                        "calm": weighted_probs.get("neutral", 0.0) * 0.3,  # Estimate calm from neutral
                        "happy": weighted_probs.get("happy", 0.0),
                        "sad": weighted_probs.get("sad", 0.0),
                        "angry": weighted_probs.get("angry", 0.0),
                        "fearful": weighted_probs.get("fear", 0.0),
                        "disgust": weighted_probs.get("disgust", 0.0),
                        "surprised": weighted_probs.get("surprise", 0.0)
                    }
                    
                    # Normalize probabilities to sum to 1
                    total = sum(face_probs.values())
                    if total > 0:
                        face_probs = {k: v/total for k, v in face_probs.items()}
                    
                    face_label = max(face_probs, key=face_probs.get)
                    face_confidence = face_probs[face_label]
                else:
                    face_probs = self._stub_probs()
                    face_label = "neutral"
                    face_confidence = 0.7
            except Exception as e:
                print(f"⚠️  FER failed: {e}")
                import traceback
                traceback.print_exc()
                face_probs = self._stub_probs()
                face_label = "neutral"
                face_confidence = 0.7
        else:
            face_probs = self._stub_probs()
            face_label = "neutral"
            face_confidence = 0.7
        
        # Audio emotion (real model or stub)
        if self.audio_model:
            try:
                # Extract audio from video to WAV using moviepy
                import tempfile
                import os
                from moviepy.editor import VideoFileClip
                
                # Create temp WAV file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                    wav_path = tmp_wav.name
                
                # Extract audio using moviepy
                video_clip = VideoFileClip(video_path)
                if video_clip.audio is not None:
                    video_clip.audio.write_audiofile(
                        wav_path,
                        fps=16000,
                        nbytes=2,
                        codec='pcm_s16le',
                        logger=None  # Suppress moviepy logs
                    )
                    video_clip.close()
                    
                    # Predict emotion
                    audio_result = self.audio_model.predict_from_path(wav_path)
                    audio_label = audio_result["label"]
                    audio_probs = audio_result["probs"]
                    audio_confidence = audio_probs[audio_label]
                    
                    print(f"✅ Audio emotion detected: {audio_label} ({audio_confidence:.2%})")
                else:
                    print("⚠️  No audio track in video")
                    raise Exception("No audio track")
                
                # Clean up
                os.remove(wav_path)
                
            except Exception as e:
                print(f"⚠️  Audio prediction failed: {e}")
                import traceback
                traceback.print_exc()
                # Fall back to stub
                audio_probs = {
                    "neutral": 0.15,
                    "calm": 0.70,
                    "happy": 0.05,
                    "sad": 0.03,
                    "angry": 0.02,
                    "fearful": 0.02,
                    "disgust": 0.01,
                    "surprised": 0.02
                }
                audio_label = "calm"
                audio_confidence = 0.70
        else:
            # Stub audio
            audio_probs = {
                "neutral": 0.15,
                "calm": 0.70,
                "happy": 0.05,
                "sad": 0.03,
                "angry": 0.02,
                "fearful": 0.02,
                "disgust": 0.01,
                "surprised": 0.02
            }
            audio_label = "calm"
            audio_confidence = 0.70
        
        # Simple fusion (average)
        multimodal_probs = {
            emotion: (face_probs.get(emotion, 0) + audio_probs.get(emotion, 0)) / 2
            for emotion in self.emotions
        }
        multimodal_label = max(multimodal_probs, key=multimodal_probs.get)
        multimodal_confidence = multimodal_probs[multimodal_label]
        
        return {
            "audio": {
                "label": audio_label,
                "probs": audio_probs,
                "confidence": audio_confidence
            },
            "face": {
                "label": face_label,
                "probs": face_probs,
                "confidence": face_confidence
            },
            "multimodal": {
                "label": multimodal_label,
                "probs": multimodal_probs,
                "confidence": multimodal_confidence
            },
            "model_type": "fer_fallback"
        }
    
    def _stub_probs(self) -> Dict[str, float]:
        """Return stub probabilities"""
        return {
            "neutral": 0.70,
            "calm": 0.15,
            "happy": 0.05,
            "sad": 0.03,
            "angry": 0.02,
            "fearful": 0.02,
            "disgust": 0.01,
            "surprised": 0.02
        }
    
    def _extract_frames(self, video_path: str, num_frames: int = 16) -> np.ndarray:
        """Extract frames from video"""
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Sample frames evenly
        frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
        
        frames = []
        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                # Resize to 112x112
                frame = cv2.resize(frame, (112, 112))
                frames.append(frame)
        
        cap.release()
        
        if len(frames) < num_frames:
            # Pad with last frame
            while len(frames) < num_frames:
                frames.append(frames[-1])
        
        return np.array(frames)
    
    def _extract_audio(self, video_path: str, sr: int = 16000) -> np.ndarray:
        """Extract audio from video"""
        try:
            # Extract audio using librosa
            y, _ = librosa.load(video_path, sr=sr)
            return y
        except Exception as e:
            print(f"⚠️  Audio extraction failed: {e}")
            # Return silence
            return np.zeros(sr * 3)
    
    def _preprocess_video(self, frames: np.ndarray) -> torch.Tensor:
        """Preprocess video frames for model"""
        # Convert to tensor: (T, H, W, C) -> (1, C, T, H, W)
        frames = frames.transpose(3, 0, 1, 2)  # (C, T, H, W)
        frames = frames.astype(np.float32) / 255.0
        
        # Normalize (ImageNet stats)
        mean = np.array([0.485, 0.456, 0.406]).reshape(3, 1, 1, 1)
        std = np.array([0.229, 0.224, 0.225]).reshape(3, 1, 1, 1)
        frames = (frames - mean) / std
        
        tensor = torch.from_numpy(frames).unsqueeze(0).to(self.device)
        return tensor
    
    def _preprocess_audio(self, audio: np.ndarray) -> torch.Tensor:
        """Preprocess audio for model"""
        # Extract MFCC features
        mfcc = librosa.feature.mfcc(y=audio, sr=16000, n_mfcc=20)
        
        # Pad or truncate to fixed length
        target_length = 100
        if mfcc.shape[1] < target_length:
            mfcc = np.pad(mfcc, ((0, 0), (0, target_length - mfcc.shape[1])))
        else:
            mfcc = mfcc[:, :target_length]
        
        # Convert to tensor
        tensor = torch.from_numpy(mfcc).unsqueeze(0).unsqueeze(0).float().to(self.device)
        return tensor
