"""
Simplified Pill Detection Service
Extracts detection logic without the full protocol
For integration with backend pipeline
"""
import cv2
import numpy as np
import os
import torch
from ultralytics import YOLO
import mediapipe as mp
from typing import Dict, Any, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure PyTorch for model loading
# Check if we should disable weights_only restriction
if os.getenv('TORCH_LOAD_WEIGHTS_ONLY', '1') == '0':
    # Monkey-patch torch.load to use weights_only=False
    original_torch_load = torch.load
    def safe_torch_load(*args, **kwargs):
        kwargs['weights_only'] = False
        return original_torch_load(*args, **kwargs)
    torch.load = safe_torch_load
    logger.info("✅ Configured PyTorch to allow all pickle objects (weights_only=False)")
else:
    logger.info("⚠️  PyTorch weights_only=True (secure mode)")


class SimplePillDetector:
    """
    Simplified detector for backend integration
    Analyzes video and returns compliance score
    """
    
    def __init__(self, model_path: str):
        """
        Initialize detector with trained model
        
        Args:
            model_path: Path to best.pt file
        """
        logger.info(f"Loading YOLOv11 model from {model_path}...")
        self.model = YOLO(model_path)
        logger.info("✅ YOLOv11 model loaded successfully")
        
        logger.info("Initializing MediaPipe Face Mesh...")
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        logger.info("✅ MediaPipe Face Mesh initialized")
        
        # Class names from training
        self.classes = ['pill', 'pill-on-tongue', 'tongue-no-pill', 'hand']
        
        # Confidence thresholds (from proto.py)
        self.thresholds = {
            'pill': 0.7,
            'pill-on-tongue': 0.4,
            'tongue-no-pill': 0.5,
            'hand': 0.75
        }
        
    def analyze_video(
        self,
        video_path: str,
        sample_rate: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze video for medication compliance
        
        Args:
            video_path: Path to video file
            sample_rate: Process 1 frame every N frames
            
        Returns:
            Compliance analysis results
        """
        logger.info(f"Analyzing video: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        logger.info(f"Video: {total_frames} frames @ {fps:.1f} FPS = {duration:.1f}s")
        
        # Storage for detections across frames
        detections_per_class = {cls: [] for cls in self.classes}
        mouth_open_frames = 0
        mouth_closed_frames = 0
        total_processed = 0
        
        frame_num = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Sample frames
            if frame_num % sample_rate == 0:
                # Run YOLO detection
                results = self.model(frame, verbose=False, conf=0.1)[0]
                
                # Extract detections
                for box in results.boxes:
                    conf = float(box.conf.item())
                    cls_id = int(box.cls.item())
                    
                    if cls_id < len(self.model.names):
                        class_name = self.model.names[cls_id]
                        if class_name in self.classes:
                            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                            
                            detections_per_class[class_name].append({
                                'confidence': conf,
                                'bbox': {
                                    'x': x1,
                                    'y': y1,
                                    'width': x2 - x1,
                                    'height': y2 - y1
                                },
                                'frame': frame_num
                            })
                
                # Check jaw position
                jaw_distance = self._get_jaw_distance(frame)
                if jaw_distance:
                    if jaw_distance > 20:  # Mouth open
                        mouth_open_frames += 1
                    elif jaw_distance < 5:  # Mouth closed
                        mouth_closed_frames += 1
                
                total_processed += 1
            
            frame_num += 1
        
        cap.release()
        
        logger.info(f"Processed {total_processed} frames out of {total_frames}")
        logger.info(f"Detections: pill={len(detections_per_class['pill'])}, "
                   f"pill-on-tongue={len(detections_per_class['pill-on-tongue'])}, "
                   f"tongue={len(detections_per_class['tongue-no-pill'])}, "
                   f"hand={len(detections_per_class['hand'])}")
        
        # Aggregate results
        results = self._aggregate_results(
            detections_per_class,
            mouth_open_frames,
            mouth_closed_frames,
            total_processed,
            duration
        )
        
        logger.info(f"✅ Analysis complete: compliance={results['compliance']}, "
                   f"score={results['compliance_score']:.2f}")
        
        return results
    
    def _get_jaw_distance(self, frame: np.ndarray) -> Optional[float]:
        """Calculate jaw opening distance"""
        try:
            h, w, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_results = self.face_mesh.process(rgb_frame)
            
            if mp_results.multi_face_landmarks:
                landmarks = mp_results.multi_face_landmarks[0].landmark
                upper_lip_y = landmarks[13].y * h  # Upper lip
                lower_lip_y = landmarks[14].y * h  # Lower lip
                return abs(lower_lip_y - upper_lip_y)
        except:
            pass
        
        return None
    
    def _aggregate_results(
        self,
        detections: Dict[str, List],
        mouth_open: int,
        mouth_closed: int,
        total_frames: int,
        duration: float
    ) -> Dict[str, Any]:
        """
        Aggregate all detections into compliance score
        """
        # Count high-confidence detections
        pill_detections = [d for d in detections['pill'] if d['confidence'] > self.thresholds['pill']]
        pill_on_tongue = [d for d in detections['pill-on-tongue'] if d['confidence'] > self.thresholds['pill-on-tongue']]
        tongue_no_pill = [d for d in detections['tongue-no-pill'] if d['confidence'] > self.thresholds['tongue-no-pill']]
        hand_detections = [d for d in detections['hand'] if d['confidence'] > self.thresholds['hand']]
        
        # Determine compliance based on detection pattern
        pill_detected = len(pill_detections) > 0
        pill_on_tongue_detected = len(pill_on_tongue) > 0
        tongue_shown = len(tongue_no_pill) > 0
        hand_detected = len(hand_detections) > 0
        mouth_opened = mouth_open > (total_frames * 0.2)  # 20% of frames
        mouth_was_closed = mouth_closed > (total_frames * 0.2)
        
        # Compliance logic based on protocol completeness
        if pill_detected and pill_on_tongue_detected and tongue_shown and mouth_was_closed:
            # Full protocol detected
            compliance = True
            compliance_score = 0.95
            verification_status = "compliant"
        elif pill_detected and pill_on_tongue_detected and mouth_opened:
            # Good compliance - pill placed on tongue
            compliance = True
            compliance_score = 0.85
            verification_status = "compliant"
        elif pill_detected and hand_detected and mouth_opened:
            # Partial compliance - pill + hand + mouth open
            compliance = True
            compliance_score = 0.75
            verification_status = "partially_compliant"
        elif pill_detected or pill_on_tongue_detected:
            # Pill detected but incomplete protocol
            compliance = True
            compliance_score = 0.60
            verification_status = "partially_compliant"
        else:
            # No clear evidence of medication
            compliance = False
            compliance_score = 0.20
            verification_status = "non_compliant"
        
        # Get best detections for display
        all_detections = []
        for class_name, det_list in detections.items():
            # Sort by confidence and take top 3 per class
            sorted_dets = sorted(det_list, key=lambda x: x['confidence'], reverse=True)
            for det in sorted_dets[:3]:
                all_detections.append({
                    'class': class_name,
                    'confidence': det['confidence'],
                    'bbox': det['bbox']
                })
        
        # Sort all by confidence
        all_detections.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Get highest confidence overall
        max_confidence = max([d['confidence'] for d in all_detections]) if all_detections else 0.0
        
        return {
            'pill_detected': pill_detected,
            'hand_detected': hand_detected,
            'face_detected': mouth_opened or mouth_was_closed,
            'compliance': compliance,
            'compliance_score': compliance_score,
            'verification_status': verification_status,
            'confidence': max_confidence,
            'objects_detected': all_detections[:10],  # Top 10 detections
            'frames_analyzed': total_frames,
            'duration_seconds': duration,
            'status': 'success',
            'protocol_completeness': {
                'pill_in_hand': pill_detected,
                'pill_on_tongue': pill_on_tongue_detected,
                'tongue_verification': tongue_shown,
                'hand_present': hand_detected,
                'mouth_opened': mouth_opened,
                'mouth_closed': mouth_was_closed
            },
            'detection_counts': {
                'pill': len(pill_detections),
                'pill_on_tongue': len(pill_on_tongue),
                'tongue_no_pill': len(tongue_no_pill),
                'hand': len(hand_detections)
            }
        }
