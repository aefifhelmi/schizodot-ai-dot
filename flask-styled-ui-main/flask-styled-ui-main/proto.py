import time
import collections
import cv2
import numpy as np
from ultralytics import YOLO
import mediapipe as mp
from flask import Flask, Response, jsonify
from flask_cors import CORS
import threading
import webbrowser

# --- Flask Setup ---
app = Flask(__name__)
CORS(app)

# Global monitor instance and lock for thread-safe access
monitor = None
monitor_lock = threading.Lock()

# --- Configuration ---
YOLO_OBJ_WEIGHT_PATH = r"C:\Users\User\Desktop\Dot Project\runs\detect\train4\weights\best.pt"

# --- MEDIAPIPE JAW TRACKING CONFIG ---
UPPER_LIP_ID = 13
LOWER_LIP_ID = 14
MOUTH_OPEN_THRESHOLD = 20
MOUTH_CLOSURE_THRESHOLD = 5

# Confidence Thresholds
CPill_P1_MIN = 0.8
CPill_P3_MIN = 0.4
CTONGUE_MIN = 0.5
CTongue_P4_MAX = 0.2
CPill_P6_MAX = 0.1
CHAND_MIN = 0.75

# Stability Check
PILL_STATIONARY_FRAMES = 60
CONCEALMENT_FRAMES = 50
FINAL_CONFIRMATION_FRAMES = 60
STABILITY_THRESHOLD = 5
VERIFIED_PASS = "VERIFIED (PASS)"
STABILIZATION_FRAMES = 20

# Text Display Configuration
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 1
COLOR_PROMPT = (0, 255, 255)
COLOR_STATUS = (0, 255, 0)
COLOR_FAIL = (0, 0, 255)
LINE_THICKNESS = 2

TARGET_CLASSES = ['pill', 'pill-on-tongue', 'tongue-no-pill', 'hand']

mp_face_mesh = mp.solutions.face_mesh


def _convert_bbox_to_xyxy(bbox_info):
    if bbox_info is None: return None
    cx, cy, w, h = bbox_info
    x1 = int(cx - w / 2); y1 = int(cy - h / 2)
    x2 = int(cx + w / 2); y2 = int(cy + h / 2)
    return (x1, y1, x2, y2)


class YOLOv11MedicationMonitor:
    def __init__(self, obj_weights_path, video_source=0, max_frames=200):
        self.obj_weights_path = obj_weights_path
        self.video_source = video_source
        self.max_frames = max_frames
        self.current_phase = 1
        self.pill_history = collections.deque(maxlen=PILL_STATIONARY_FRAMES)
        self.final_confirm_counter = 0
        self.current_frame = None  # For Flask streaming
        self.result_status = "INITIALIZING"  # For Flask status endpoint
        self.should_reset = False  # Flag to trigger protocol restart

        self.obj_model = self._load_yolo_model(self.obj_weights_path, name='Object')

        self.face_mesh_detector = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        self.cap = None

    def _load_yolo_model(self, weights_path, name):
        try:
            print(f"Loading {name} Model from: {weights_path}...")
            model = YOLO(weights_path)
            print(f"✅ {name} Model loaded successfully.")
            return model
        except Exception as e:
            print(f"⚠️ Error loading {name} model from {weights_path}. Using MOCK fallback. Error: {e}")
            return "MOCK"

    def _get_mock_detections(self):
        mock_detections = {cls: (0.0, None) for cls in TARGET_CLASSES}

        if self.current_phase == 2:
            mock_detections['jaw_distance'] = 30
        elif self.current_phase == 4:
            mock_detections['jaw_distance'] = 5

        if self.current_phase == 1:
            mock_detections['pill'] = (0.95, (100, 100, 20, 20))
        elif self.current_phase == 2 or self.current_phase == 5 or self.current_phase == 6:
            mock_detections['tongue-no-pill'] = (0.9, (350, 450, 110, 55))
        elif self.current_phase == 3:
            mock_detections['pill-on-tongue'] = (0.9, (450, 500, 15, 15))

        return mock_detections

    def _calculate_jaw_drop(self, mp_landmarks, h):
        if not mp_landmarks: return 9999, False
        landmarks = mp_landmarks[0].landmark
        UL_Y = landmarks[UPPER_LIP_ID].y * h
        LL_Y = landmarks[LOWER_LIP_ID].y * h
        vertical_distance = abs(LL_Y - UL_Y)
        return vertical_distance, True

    def _yolo_detect(self, frame):
        if self.obj_model == "MOCK": return self._get_mock_detections()

        detections = {cls: (0.0, None) for cls in TARGET_CLASSES}
        detections['jaw_distance'] = 0.0
        detections['lip_landmarks'] = None

        try:
            obj_results = self.obj_model(frame, verbose=False, conf=0.1)[0]
            class_names = self.obj_model.names

            for box in obj_results.boxes:
                conf = box.conf.item(); cls = int(box.cls.item())
                label = class_names[cls] if cls < len(class_names) else None
                if label in TARGET_CLASSES:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist()); w, h = x2 - x1, y2 - y1; cx, cy = x1 + w // 2, y1 + h // 2
                    if conf > detections[label][0]: detections[label] = (conf, (cx, cy, w, h))

            h, w, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_results = self.face_mesh_detector.process(rgb_frame)

            if mp_results.multi_face_landmarks:
                jaw_drop, _ = self._calculate_jaw_drop(mp_results.multi_face_landmarks, h)
                detections['jaw_distance'] = jaw_drop
                detections['lip_landmarks'] = mp_results.multi_face_landmarks[0].landmark

        except Exception:
            return self._get_mock_detections()

        return detections

    def _check_detection(self, detections, object_name, min_conf):
        conf, _ = detections.get(object_name, (0.0, None))
        return conf >= min_conf

    def _check_absence(self, detections, object_name, max_conf):
        conf, _ = detections.get(object_name, (0.0, None))
        return conf < max_conf

    def _calculate_centroid(self, bbox_info):
        if bbox_info is None: return None
        cx, cy, _, _ = bbox_info
        return (cx, cy)

    def run_protocol(self):
        self.cap = cv2.VideoCapture(self.video_source)
        is_camera_open = self.cap.isOpened()

        if not is_camera_open:
            print(f"❌ Error: Could not open video source {self.video_source}. Running in MOCK mode only.")
            self.obj_model = "MOCK"

        print("--- Starting YOLOv11 Adherence Protocol (Continuous Mode) ---")
        
        # Continuous loop to allow restarts
        while True:
            # Reset all variables for new session
            frame_count = 0
            self.current_phase = 1
            self.result_status = "RUNNING"
            face_loss_counter = 0
            final_confirm_counter = 0
            phase_4_counter = 0
            warning_message = ""
            self.pill_history.clear()
            self.should_reset = False
            
            print(f"🔄 Starting protocol session (Phase 1)")

            while self.current_phase <= 6 and not self.should_reset:
            frame_count += 1
            frame = None
            if is_camera_open:
                ret, frame = self.cap.read()
                if not ret: break
            if frame is None: frame = np.zeros((480, 640, 3), dtype=np.uint8)

            h, w, _ = frame.shape
            warning_message = ""

            detections = self._yolo_detect(frame)
            vertical_jaw_drop = detections.get('jaw_distance', 0.0)

            status_text = f"Phase {self.current_phase} (Awaiting Action)"

            face_landmarks_found = detections.get('lip_landmarks') is not None

            if frame_count > STABILIZATION_FRAMES:
                if not face_landmarks_found:
                    face_loss_counter += 1
                    if face_loss_counter >= PILL_STATIONARY_FRAMES:
                        print(f"\n--- ❌ FATAL FAILURE: MOUTH AREA COVERED OR LOST FOR 2 SECONDS ---")
                        self.result_status = "FATAL FAILURE (MOUTH COVERED)"
                        break
                else:
                    face_loss_counter = 0

            prompts = {1: "PHASE 1: Hold medication up.", 2: "PHASE 2: Open mouth WIDE (Check).",
                       3: "PHASE 3: Place pill on your tongue.", 4: "PHASE 4: Close mouth (Check).",
                       5: "PHASE 5: Open mouth for check.", 6: "PHASE 6: SWALLOW CHECK..."}
            prompt_text = prompts.get(self.current_phase, "Protocol Starting...")
            cv2.putText(frame, prompt_text, (10, 50), FONT, FONT_SCALE, COLOR_PROMPT, LINE_THICKNESS, cv2.LINE_AA)

            if self.current_phase == 1:
                if self._check_detection(detections, 'pill', CPill_P1_MIN):
                    status_text = "SUCCESS: Pill Detected. Advancing..."; self.current_phase = 2
                else:
                    cv2.putText(frame, "Pill NOT Detected!", (10, 90), FONT, FONT_SCALE, COLOR_FAIL, LINE_THICKNESS, cv2.LINE_AA)

            elif self.current_phase == 2:
                tongue_present = self._check_detection(detections, 'tongue-no-pill', CTONGUE_MIN)
                jaw_open = vertical_jaw_drop > MOUTH_OPEN_THRESHOLD

                if tongue_present and jaw_open:
                    status_text = "SUCCESS: Mouth Wide Open. Advancing..."; self.current_phase = 3
                else:
                    cv2.putText(frame, f"Open mouth WIDER! (Drop: {vertical_jaw_drop:.1f}px)", (10, 90), FONT, FONT_SCALE, COLOR_FAIL, LINE_THICKNESS, cv2.LINE_AA)

            elif self.current_phase == 3:
                pill_on_tongue_present = self._check_detection(detections, 'pill-on-tongue', CPill_P3_MIN)

                if pill_on_tongue_present:
                    current_centroid = self._calculate_centroid(detections['pill-on-tongue'][1])
                    if current_centroid:
                        self.pill_history.append(current_centroid)
                    else:
                        self.pill_history.clear()

                    if len(self.pill_history) >= PILL_STATIONARY_FRAMES:
                        status_text = "SUCCESS: Pill Stable (Duration Met). Advancing..."; self.current_phase = 4; self.pill_history.clear()
                    else:
                        status_text = f"HOLD: {len(self.pill_history)}/{PILL_STATIONARY_FRAMES} frames steady"
                else:
                    self.pill_history.clear()
                    cv2.putText(frame, "Place pill on tongue and hold!", (10, 90), FONT, FONT_SCALE, COLOR_FAIL, LINE_THICKNESS, cv2.LINE_AA)

            elif self.current_phase == 4:
                tongue_absent_in_frame = self._check_absence(detections, 'tongue-no-pill', CTongue_P4_MAX)
                jaw_closed_in_frame = vertical_jaw_drop < MOUTH_CLOSURE_THRESHOLD
                pill_on_tongue_conf = detections.get('pill-on-tongue', (0.0, None))[0]

                if phase_4_counter > 0 and (vertical_jaw_drop > MOUTH_OPEN_THRESHOLD) and (pill_on_tongue_conf < CPill_P3_MIN):
                    print(f"--- ⚠️ PHASE 4 RESET: Mouth opened wide ({vertical_jaw_drop:.1f}) but no pill on tongue detected ({pill_on_tongue_conf:.2f}). ---")
                    phase_4_counter = 0
                    warning_message = "MEDICATION MISSING (Resetting P4)"

                if tongue_absent_in_frame and jaw_closed_in_frame:
                    if phase_4_counter < CONCEALMENT_FRAMES:
                        phase_4_counter += 1
                        status_text = f"HOLD CLOSE: {phase_4_counter}/{CONCEALMENT_FRAMES} frames"
                    else:
                        status_text = "SUCCESS: Mouth Closed. Advancing..."; self.current_phase = 5; phase_4_counter = 0
                else:
                    if phase_4_counter > 0 and not warning_message:
                        phase_4_counter = 0
                        warning_message = "Mouth Opened Too Early!"

                    feedback = []
                    if not tongue_absent_in_frame: feedback.append("Medication Missing!.")
                    if not jaw_closed_in_frame: feedback.append(f"Jaws not fully closed (Drop: {vertical_jaw_drop:.1f}px).")

                    if not warning_message:
                        cv2.putText(frame, "Please close your mouth completely!", (10, 90), FONT, 0.7, COLOR_FAIL, LINE_THICKNESS, cv2.LINE_AA)
                        cv2.putText(frame, f"Failure: {', '.join(feedback)}", (10, 120), FONT, 0.6, COLOR_FAIL, 1, cv2.LINE_AA)

            elif self.current_phase == 5:
                pill_on_tongue_conf = detections.get('pill-on-tongue', (0.0, None))[0]

                if pill_on_tongue_conf >= CPill_P3_MIN:
                    print(f"\n--- ❌ FATAL FAILURE: PILL DETECTED ON TONGUE AFTER CONCEALMENT ---")
                    self.result_status = "FATAL FAILURE (PILL REAPPEARED)"
                    break

                if self._check_detection(detections, 'tongue-no-pill', CTONGUE_MIN):
                    status_text = "SUCCESS: Re-opened mouth. Checking swallow..."; self.current_phase = 6
                else:
                    cv2.putText(frame, "Open mouth wide again and show tongue!", (10, 90), FONT, 0.7, COLOR_FAIL, LINE_THICKNESS, cv2.LINE_AA)

            elif self.current_phase == 6:
                tongue_no_pill_confirmed = self._check_detection(detections, 'tongue-no-pill', CTONGUE_MIN)
                pill_gone = self._check_absence(detections, 'pill', CPill_P6_MAX)

                if tongue_no_pill_confirmed and pill_gone:
                    final_confirm_counter += 1

                    if final_confirm_counter >= FINAL_CONFIRMATION_FRAMES:
                        status_text = VERIFIED_PASS
                        print(f"\n--- 🎉 PROTOCOL COMPLETE! {VERIFIED_PASS} ---"); self.result_status = VERIFIED_PASS; break
                    else:
                        status_text = f"FINAL CHECK: Hold for {FINAL_CONFIRMATION_FRAMES - final_confirm_counter} more frames."

                else:
                    final_confirm_counter = 0
                    status_text = "FAILURE: Pill still visible! SWALLOW NOW!"

                    feedback = []
                    if not tongue_no_pill_confirmed: feedback.append("Mouth must be open")
                    if not pill_gone: feedback.append("Pill is still detected (SWALLOW!)")

                    cv2.putText(frame, status_text, (10, 90), FONT, 0.7, COLOR_FAIL, LINE_THICKNESS, cv2.LINE_AA)
                    cv2.putText(frame, f"Issue: {', '.join(feedback)}", (10, 120), FONT, 0.6, COLOR_FAIL, 1, cv2.LINE_AA)

            color_final_status = COLOR_STATUS if status_text.startswith("SUCCESS") or status_text == VERIFIED_PASS else (255, 255, 255)
            cv2.putText(frame, status_text, (10, frame.shape[0] - 10), FONT, 0.7, color_final_status, LINE_THICKNESS, cv2.LINE_AA)

            if warning_message:
                cv2.putText(frame, warning_message, (10, 90), FONT, 0.7, COLOR_FAIL, LINE_THICKNESS, cv2.LINE_AA)

            if detections.get('lip_landmarks'):
                landmarks = detections['lip_landmarks']
                UL_X = int(landmarks[UPPER_LIP_ID].x * w); UL_Y = int(landmarks[UPPER_LIP_ID].y * h)
                LL_X = int(landmarks[LOWER_LIP_ID].x * w); LL_Y = int(landmarks[LOWER_LIP_ID].y * h)

                cv2.circle(frame, (UL_X, UL_Y), 3, (0, 0, 255), -1)
                cv2.circle(frame, (LL_X, LL_Y), 3, (0, 255, 0), -1)
                cv2.line(frame, (UL_X, UL_Y), (LL_X, LL_Y), (255, 255, 0), 1)

                vertical_jaw_drop = detections.get('jaw_distance', 0.0)
                cv2.putText(frame, f"Drop: {vertical_jaw_drop:.1f} px (Target < {MOUTH_CLOSURE_THRESHOLD})", (10, h - 30), FONT, 0.5, (0, 255, 255), 1, cv2.LINE_AA)

            mouth_conf, mouth_bbox = detections.get('mouth', (0.0, None))
            if mouth_conf >= 0.5:
                xyxy = _convert_bbox_to_xyxy(mouth_bbox); color = (255, 100, 0)
                cv2.rectangle(frame, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), color, 1)
                text = f"Mouth: {mouth_conf:.2f}"
                cv2.putText(frame, text, (xyxy[0], xyxy[3] + 15), FONT, 0.5, color, 1, cv2.LINE_AA)

            pill_on_tongue_conf, pill_on_tongue_bbox = detections.get('pill-on-tongue', (0.0, None))
            if pill_on_tongue_conf >= 0.1:
                xyxy = _convert_bbox_to_xyxy(pill_on_tongue_bbox); color = (255, 0, 255)
                cv2.rectangle(frame, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), color, LINE_THICKNESS)
                text = f"P-on-T: {pill_on_tongue_conf:.2f}"
                cv2.putText(frame, text, (xyxy[0], xyxy[1] - 5), FONT, 0.6, color, LINE_THICKNESS, cv2.LINE_AA)

            pill_conf, pill_bbox = detections.get('pill', (0.0, None))
            if pill_conf >= 0.7 and self.current_phase < 4:
                xyxy = _convert_bbox_to_xyxy(pill_bbox); color = (0, 255, 255)
                cv2.rectangle(frame, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), color, LINE_THICKNESS)
                text = f"Pill: {pill_conf:.2f}"
                cv2.putText(frame, text, (xyxy[0], xyxy[1] - 5), FONT, 0.6, color, LINE_THICKNESS, cv2.LINE_AA)

            # Store frame for Flask streaming
            with monitor_lock:
                self.current_frame = frame.copy()

            if is_camera_open:
                cv2.imshow('YOLO Medication Monitor (MediaPipe Jaw Check)', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("\nUser manually quit the protocol."); self.result_status = "USER QUIT"; break

            time.sleep(0.03)
            
            # Check if reset was requested
            if self.should_reset:
                print("🔄 Reset requested, restarting protocol...")
                break

        # If protocol ended naturally, wait for reset
        if not self.should_reset:
            print(f"\n--- PROTOCOL SESSION ENDED: {self.result_status} ---")
            print("Waiting for reset to start new session...")
            while not self.should_reset:
                time.sleep(0.1)


# --- Flask Routes ---
@app.route('/')
def index():
    return jsonify({"status": "Flask backend running"})


def generate_frames():
    """Generator function for video streaming"""
    while True:
        with monitor_lock:
            if monitor and monitor.current_frame is not None:
                frame = monitor.current_frame.copy()
            else:
                # Create a blank frame if no frame available
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, "Waiting for camera...", (50, 240), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        time.sleep(0.033)  # ~30 FPS


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/status_update')
def status_update():
    with monitor_lock:
        if monitor:
            return jsonify({
                "result_status": monitor.result_status,
                "current_phase": monitor.current_phase
            })
        else:
            return jsonify({
                "result_status": "DISCONNECTED",
                "current_phase": 0
            })


@app.route('/reset', methods=['POST'])
def reset_protocol():
    """Reset the protocol to start over"""
    global monitor
    with monitor_lock:
        if monitor:
            # Set reset flag to trigger protocol restart
            monitor.should_reset = True
            print("🔄 Protocol reset requested by user")
            return jsonify({"status": "success", "message": "Protocol reset initiated"})
        else:
            return jsonify({"status": "error", "message": "Monitor not initialized"}), 500


def open_browser():
    """Open browser after a short delay"""
    time.sleep(1.5)
    monitor_url = "https://850180c3-60a2-4930-a17f-4f1427dc94ce.lovableproject.com/monitor"
    print(f"🌐 Opening browser to: {monitor_url}")
    webbrowser.open(monitor_url)


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting Medication Adherence Protocol System")
    print("=" * 60)
    
    # Initialize monitor
    monitor = YOLOv11MedicationMonitor(
        obj_weights_path=YOLO_OBJ_WEIGHT_PATH,
        video_source=0,
        max_frames=200
    )
    
    # Start protocol in separate thread
    protocol_thread = threading.Thread(target=monitor.run_protocol, daemon=True)
    protocol_thread.start()
    print("✅ Protocol thread started")
    
    # Start browser opener in separate thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Start Flask server
    print("✅ Starting Flask server on http://localhost:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)
