"""
Real-time Medication Compliance Protocol Service
Based on proto.py but integrated with backend API
Uses WebSocket for real-time video streaming and status updates
"""
import cv2
import numpy as np
import collections
import torch
from ultralytics import YOLO
import mediapipe as mp
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading
import time
from datetime import datetime
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration
MODEL_PATH = os.getenv("MODEL_PATH", "./models/best.pt")
DEVICE = os.getenv("DEVICE", "cpu")

# Protocol Constants (from proto.py)
UPPER_LIP_ID = 13
LOWER_LIP_ID = 14
MOUTH_OPEN_THRESHOLD = 20
MOUTH_CLOSURE_THRESHOLD = 5

CPill_P1_MIN = 0.8
CPill_P3_MIN = 0.4
CTONGUE_MIN = 0.5
CTongue_P4_MAX = 0.2
CPill_P6_MAX = 0.1
CHAND_MIN = 0.75

PILL_STATIONARY_FRAMES = 60
CONCEALMENT_FRAMES = 50
FINAL_CONFIRMATION_FRAMES = 60
VERIFIED_PASS = "VERIFIED (PASS)"

TARGET_CLASSES = ['pill', 'pill-on-tongue', 'tongue-no-pill', 'hand']

# Global monitor instance
monitor = None
monitor_lock = threading.Lock()

# Preload model on startup for faster session creation
logger.info("=" * 60)
logger.info("⚙️  Preloading YOLOv11 model...")
logger.info("=" * 60)
try:
    import os
    _model_path = os.getenv("MODEL_PATH", "./models/best.pt")
    logger.info(f"Loading model from: {_model_path}")
    
    # Configure PyTorch
    if os.getenv('TORCH_LOAD_WEIGHTS_ONLY', '1') == '0':
        original_torch_load = torch.load
        def safe_torch_load(*args, **kwargs):
            kwargs['weights_only'] = False
            return original_torch_load(*args, **kwargs)
        torch.load = safe_torch_load
    
    _global_model = YOLO(_model_path)
    logger.info(f"✅ Model loaded! Classes: {list(_global_model.names.values())}")
    logger.info("✅ MediaPipe Face Mesh ready")
except Exception as e:
    logger.error(f"❌ Failed to preload model: {e}")
    _global_model = None


class RealtimeComplianceMonitor:
    """
    Real-time compliance monitoring with 6-phase protocol
    Adapted from proto.py for backend integration
    """
    
    def __init__(self, patient_id: str, session_id: str):
        global _global_model
        
        self.patient_id = patient_id
        self.session_id = session_id
        self.current_phase = 1
        self.result_status = "INITIALIZING"
        self.current_frame = None
        self.should_stop = False
        
        # Protocol tracking
        self.pill_history = collections.deque(maxlen=PILL_STATIONARY_FRAMES)
        self.final_confirm_counter = 0
        self.phase_4_counter = 0
        self.face_loss_counter = 0
        
        # Use preloaded model or load new one
        logger.info(f"🔧 Initializing monitor for patient {patient_id}, session {session_id}")
        
        if _global_model is not None:
            self.model = _global_model
            logger.info("✅ Using preloaded YOLO model")
        else:
            logger.warning("⚠️  Preloaded model not available, loading new instance...")
            self.model = YOLO(MODEL_PATH)
            logger.info("✅ YOLO model loaded")
        
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        
        logger.info(f"✅ Session ready - Model classes: {list(self.model.names.values())}")
    
    def _yolo_detect(self, frame):
        """Run YOLO detection on frame"""
        detections = {cls: (0.0, None) for cls in TARGET_CLASSES}
        detections['jaw_distance'] = 0.0
        detections['lip_landmarks'] = None
        
        try:
            # YOLO object detection
            results = self.model(frame, verbose=False, conf=0.1)[0]
            class_names = self.model.names
            
            # Debug: Log detection count every 60 frames
            if not hasattr(self, '_debug_frame_count'):
                self._debug_frame_count = 0
            self._debug_frame_count += 1
            
            if self._debug_frame_count % 60 == 0:
                logger.info(f"🔍 YOLO running: {len(results.boxes)} objects detected in frame")
            
            for box in results.boxes:
                conf = box.conf.item()
                cls = int(box.cls.item())
                label = class_names[cls] if cls < len(class_names) else None
                
                if label in TARGET_CLASSES:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    w, h = x2 - x1, y2 - y1
                    cx, cy = x1 + w // 2, y1 + h // 2
                    
                    if conf > detections[label][0]:
                        detections[label] = (conf, (cx, cy, w, h))
            
            # MediaPipe face mesh
            h, w, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_results = self.face_mesh.process(rgb_frame)
            
            if mp_results.multi_face_landmarks:
                landmarks = mp_results.multi_face_landmarks[0].landmark
                UL_Y = landmarks[UPPER_LIP_ID].y * h
                LL_Y = landmarks[LOWER_LIP_ID].y * h
                jaw_drop = abs(LL_Y - UL_Y)
                detections['jaw_distance'] = jaw_drop
                detections['lip_landmarks'] = landmarks
                
                # Debug: Log MediaPipe detection
                if self._debug_frame_count % 60 == 0:
                    logger.info(f"👄 MediaPipe: Face detected, jaw distance = {jaw_drop:.1f}px")
            else:
                if self._debug_frame_count % 60 == 0:
                    logger.warning("⚠️  MediaPipe: No face detected in frame")
        
        except Exception as e:
            logger.error(f"Detection error: {e}")
        
        return detections
    
    def _check_detection(self, detections, object_name, min_conf):
        """Check if object detected above threshold"""
        conf, _ = detections.get(object_name, (0.0, None))
        return conf >= min_conf
    
    def _check_absence(self, detections, object_name, max_conf):
        """Check if object absent (below threshold)"""
        conf, _ = detections.get(object_name, (0.0, None))
        return conf < max_conf
    
    def _calculate_centroid(self, bbox_info):
        """Calculate centroid from bbox"""
        if bbox_info is None:
            return None
        cx, cy, _, _ = bbox_info
        return (cx, cy)
    
    def _draw_detections(self, frame, detections):
        """Draw bounding boxes for detected objects (like proto.py)"""
        # Define colors for each class (BGR format)
        colors = {
            'pill': (0, 255, 255),           # Yellow
            'pill-on-tongue': (255, 0, 255),  # Magenta
            'tongue-no-pill': (0, 255, 0),    # Green
            'hand': (255, 0, 0)               # Blue
        }
        
        # Define minimum confidence thresholds per class
        min_conf_thresholds = {
            'pill': 0.7,              # Higher threshold for pill detection
            'pill-on-tongue': 0.1,
            'tongue-no-pill': 0.1,
            'hand': 0.1
        }
        
        # Draw each detection
        for class_name in TARGET_CLASSES:
            conf, bbox_info = detections.get(class_name, (0.0, None))
            
            # Get threshold for this class
            min_conf = min_conf_thresholds.get(class_name, 0.1)
            
            # Skip if confidence too low or no bbox
            if conf < min_conf or bbox_info is None:
                continue
            
            # Convert bbox from (cx, cy, w, h) to (x1, y1, x2, y2)
            cx, cy, w, h = bbox_info
            x1 = int(cx - w / 2)
            y1 = int(cy - h / 2)
            x2 = int(cx + w / 2)
            y2 = int(cy + h / 2)
            
            # Get color for this class
            color = colors.get(class_name, (128, 128, 128))
            
            # Draw rectangle
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label with confidence
            label = f"{class_name}: {conf:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            
            # Draw label background
            cv2.rectangle(frame, (x1, y1 - label_size[1] - 4), 
                         (x1 + label_size[0], y1), color, -1)
            
            # Draw label text
            cv2.putText(frame, label, (x1, y1 - 2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        
        # Draw jaw tracking lines if face detected
        if detections.get('lip_landmarks') is not None:
            landmarks = detections['lip_landmarks']
            h, w, _ = frame.shape
            
            # Upper and lower lip positions
            UL_X = int(landmarks[UPPER_LIP_ID].x * w)
            UL_Y = int(landmarks[UPPER_LIP_ID].y * h)
            LL_X = int(landmarks[LOWER_LIP_ID].x * w)
            LL_Y = int(landmarks[LOWER_LIP_ID].y * h)
            
            # Draw lip landmarks
            cv2.circle(frame, (UL_X, UL_Y), 3, (0, 0, 255), -1)  # Red for upper
            cv2.circle(frame, (LL_X, LL_Y), 3, (0, 255, 0), -1)  # Green for lower
            cv2.line(frame, (UL_X, UL_Y), (LL_X, LL_Y), (255, 255, 0), 2)  # Yellow line
            
            # Draw jaw distance
            jaw_dist = detections.get('jaw_distance', 0.0)
            cv2.putText(frame, f"Jaw: {jaw_dist:.1f}px", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    def process_frame(self, frame):
        """
        Process a single frame through the 6-phase protocol
        Returns: (annotated_frame, status_dict)
        """
        h, w, _ = frame.shape
        detections = self._yolo_detect(frame)
        vertical_jaw_drop = detections.get('jaw_distance', 0.0)
        face_landmarks = detections.get('lip_landmarks') is not None
        
        # Status text
        status_text = f"Phase {self.current_phase}"
        message = ""
        
        # Check for face loss
        if not face_landmarks:
            self.face_loss_counter += 1
            if self.face_loss_counter >= 60:
                self.result_status = "FATAL FAILURE (MOUTH COVERED)"
                status_text = "FAILED: Face lost"
        else:
            self.face_loss_counter = 0
        
        # Phase logic (from proto.py)
        if self.current_phase == 1:
            message = "PHASE 1: Hold medication up"
            if self._check_detection(detections, 'pill', CPill_P1_MIN):
                status_text = "SUCCESS: Pill Detected"
                self.current_phase = 2
        
        elif self.current_phase == 2:
            message = "PHASE 2: Open mouth WIDE"
            tongue_present = self._check_detection(detections, 'tongue-no-pill', CTONGUE_MIN)
            jaw_open = vertical_jaw_drop > MOUTH_OPEN_THRESHOLD
            
            if tongue_present and jaw_open:
                status_text = "SUCCESS: Mouth Wide Open"
                self.current_phase = 3
            else:
                message = f"Open mouth WIDER! (Drop: {vertical_jaw_drop:.1f}px)"
        
        elif self.current_phase == 3:
            message = "PHASE 3: Place pill on your tongue"
            pill_on_tongue = self._check_detection(detections, 'pill-on-tongue', CPill_P3_MIN)
            
            if pill_on_tongue:
                centroid = self._calculate_centroid(detections['pill-on-tongue'][1])
                if centroid:
                    self.pill_history.append(centroid)
                else:
                    self.pill_history.clear()
                
                if len(self.pill_history) >= PILL_STATIONARY_FRAMES:
                    status_text = "SUCCESS: Pill Stable"
                    self.current_phase = 4
                    self.pill_history.clear()
                else:
                    status_text = f"HOLD: {len(self.pill_history)}/{PILL_STATIONARY_FRAMES}"
            else:
                self.pill_history.clear()
        
        elif self.current_phase == 4:
            message = "PHASE 4: Close mouth"
            tongue_absent = self._check_absence(detections, 'tongue-no-pill', CTongue_P4_MAX)
            jaw_closed = vertical_jaw_drop < MOUTH_CLOSURE_THRESHOLD
            
            if tongue_absent and jaw_closed:
                self.phase_4_counter += 1
                if self.phase_4_counter >= CONCEALMENT_FRAMES:
                    status_text = "SUCCESS: Mouth Closed"
                    self.current_phase = 5
                    self.phase_4_counter = 0
                else:
                    status_text = f"HOLD CLOSE: {self.phase_4_counter}/{CONCEALMENT_FRAMES}"
            else:
                self.phase_4_counter = 0
                message = "Please close your mouth completely!"
        
        elif self.current_phase == 5:
            message = "PHASE 5: Open mouth for check"
            pill_on_tongue_conf = detections.get('pill-on-tongue', (0.0, None))[0]
            
            if pill_on_tongue_conf >= CPill_P3_MIN:
                self.result_status = "FATAL FAILURE (PILL REAPPEARED)"
                status_text = "FAILED: Pill reappeared"
            elif self._check_detection(detections, 'tongue-no-pill', CTONGUE_MIN):
                status_text = "SUCCESS: Re-opened mouth"
                self.current_phase = 6
        
        elif self.current_phase == 6:
            message = "PHASE 6: SWALLOW CHECK"
            tongue_no_pill = self._check_detection(detections, 'tongue-no-pill', CTONGUE_MIN)
            pill_gone = self._check_absence(detections, 'pill', CPill_P6_MAX)
            
            if tongue_no_pill and pill_gone:
                self.final_confirm_counter += 1
                if self.final_confirm_counter >= FINAL_CONFIRMATION_FRAMES:
                    self.result_status = VERIFIED_PASS
                    status_text = VERIFIED_PASS
                else:
                    status_text = f"FINAL CHECK: {FINAL_CONFIRMATION_FRAMES - self.final_confirm_counter} frames"
            else:
                self.final_confirm_counter = 0
                status_text = "FAILURE: Pill still visible!"
        
        # Draw bounding boxes for detected objects
        self._draw_detections(frame, detections)
        
        # Draw on frame
        cv2.putText(frame, message, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, status_text, (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Store for streaming
        with monitor_lock:
            self.current_frame = frame.copy()
        
        return frame, {
            'phase': self.current_phase,
            'status': self.result_status,
            'message': message,
            'status_text': status_text,
            'jaw_distance': vertical_jaw_drop,
            'detections': {k: v[0] for k, v in detections.items() if k in TARGET_CLASSES}
        }


@app.route('/')
def index():
    """Serve the compliance monitor UI"""
    from flask import send_from_directory
    return send_from_directory('static', 'compliance_monitor.html')


@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "realtime-compliance",
        "model_loaded": True
    })


@socketio.on('connect')
def handle_connect():
    logger.info("Client connected")
    emit('status', {'message': 'Connected to compliance monitor'})


@socketio.on('start_session')
def handle_start_session(data):
    """Start a new compliance monitoring session"""
    global monitor
    
    patient_id = data.get('patient_id')
    session_id = data.get('session_id', f"session-{int(time.time())}")
    
    logger.info(f"Starting session for patient {patient_id}")
    
    with monitor_lock:
        monitor = RealtimeComplianceMonitor(patient_id, session_id)
    
    emit('session_started', {
        'patient_id': patient_id,
        'session_id': session_id,
        'status': 'ready'
    })


@socketio.on('process_frame')
def handle_frame(data):
    """Process a webcam frame through the protocol"""
    global monitor
    
    if monitor is None:
        logger.warning("⚠️  Frame received but no active session")
        emit('error', {'message': 'No active session'})
        return
    
    try:
        # Decode base64 frame
        import base64
        frame_data = base64.b64decode(data['frame'])
        nparr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            logger.error("❌ Failed to decode frame")
            emit('error', {'message': 'Failed to decode frame'})
            return
        
        # Process through protocol
        annotated_frame, status = monitor.process_frame(frame)
        
        # Log detection results every 30 frames (moved to after process_frame)
        # Frame counting is done inside _yolo_detect method
        
        # Encode annotated frame
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        encoded_frame = base64.b64encode(buffer).decode('utf-8')
        
        # Emit result
        emit('frame_result', {
            'frame': encoded_frame,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Check if protocol complete
        if status['status'] == VERIFIED_PASS:
            logger.info(f"🎉 Protocol PASSED for {monitor.patient_id}")
            emit('protocol_complete', {
                'result': 'success',
                'patient_id': monitor.patient_id,
                'session_id': monitor.session_id,
                'timestamp': datetime.utcnow().isoformat()
            })
        elif 'FAILURE' in status['status']:
            logger.warning(f"❌ Protocol FAILED for {monitor.patient_id}: {status['status']}")
            emit('protocol_complete', {
                'result': 'failed',
                'reason': status['status'],
                'patient_id': monitor.patient_id,
                'session_id': monitor.session_id,
                'timestamp': datetime.utcnow().isoformat()
            })
    
    except Exception as e:
        logger.error(f"❌ Frame processing error: {e}", exc_info=True)
        emit('error', {'message': str(e)})


@socketio.on('stop_session')
def handle_stop():
    """Stop the current session"""
    global monitor
    
    with monitor_lock:
        if monitor:
            result = {
                'patient_id': monitor.patient_id,
                'session_id': monitor.session_id,
                'final_status': monitor.result_status,
                'final_phase': monitor.current_phase
            }
            monitor = None
            emit('session_stopped', result)
        else:
            emit('error', {'message': 'No active session'})


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🎥 Starting Real-time Compliance Service")
    logger.info("=" * 60)
    socketio.run(app, host='0.0.0.0', port=8004, debug=False, allow_unsafe_werkzeug=True)
