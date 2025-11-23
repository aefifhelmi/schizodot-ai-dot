"""
Real-time Pill Detection Test
Similar to proto.py but simplified for testing
Uses webcam to show live detection results
"""
import cv2
import numpy as np
from simple_detector import SimplePillDetector
import sys

# Configuration
MODEL_PATH = "./models/best.pt"
FONT = cv2.FONT_HERSHEY_SIMPLEX
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (0, 0, 255)
COLOR_YELLOW = (0, 255, 255)
COLOR_BLUE = (255, 0, 0)


def _convert_bbox_to_xyxy(bbox_info):
    """Convert bbox dict to xyxy format"""
    if bbox_info is None:
        return None
    x = bbox_info['x']
    y = bbox_info['y']
    w = bbox_info['width']
    h = bbox_info['height']
    x1 = x
    y1 = y
    x2 = x + w
    y2 = y + h
    return (x1, y1, x2, y2)


def main():
    print("=" * 60)
    print("🎥 REAL-TIME PILL DETECTION TEST")
    print("=" * 60)
    print()
    print("Controls:")
    print("  - Press 'q' to quit")
    print("  - Press 's' to take snapshot and analyze")
    print()
    
    # Initialize detector (YOLO model)
    try:
        print("Loading YOLOv11 model...")
        from ultralytics import YOLO
        import mediapipe as mp
        
        model = YOLO(MODEL_PATH)
        print("✅ Model loaded successfully")
        
        # Initialize MediaPipe Face Mesh
        face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )
        print("✅ MediaPipe initialized")
        
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return
    
    # Open webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Error: Could not open webcam")
        return
    
    print("✅ Webcam opened")
    print()
    print("Starting real-time detection...")
    print("-" * 60)
    
    classes = ['pill', 'pill-on-tongue', 'tongue-no-pill', 'hand']
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        h, w, _ = frame.shape
        
        # Run YOLO detection
        results = model(frame, verbose=False, conf=0.1)[0]
        
        # Process detections
        detections = {}
        for box in results.boxes:
            conf = float(box.conf.item())
            cls_id = int(box.cls.item())
            
            if cls_id < len(model.names):
                class_name = model.names[cls_id]
                if class_name in classes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    
                    # Store detection
                    if class_name not in detections or conf > detections[class_name]['conf']:
                        detections[class_name] = {
                            'conf': conf,
                            'bbox': (x1, y1, x2, y2)
                        }
        
        # Check jaw position with MediaPipe
        jaw_distance = None
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_results = face_mesh.process(rgb_frame)
        
        if mp_results.multi_face_landmarks:
            landmarks = mp_results.multi_face_landmarks[0].landmark
            upper_lip_y = landmarks[13].y * h  # Upper lip
            lower_lip_y = landmarks[14].y * h  # Lower lip
            jaw_distance = abs(lower_lip_y - upper_lip_y)
            
            # Draw lip landmarks
            UL_X = int(landmarks[13].x * w)
            UL_Y = int(landmarks[13].y * h)
            LL_X = int(landmarks[14].x * w)
            LL_Y = int(landmarks[14].y * h)
            
            cv2.circle(frame, (UL_X, UL_Y), 3, (0, 0, 255), -1)
            cv2.circle(frame, (LL_X, LL_Y), 3, (0, 255, 0), -1)
            cv2.line(frame, (UL_X, UL_Y), (LL_X, LL_Y), (255, 255, 0), 1)
        
        # Draw detection boxes
        for class_name, det in detections.items():
            bbox = det['bbox']
            conf = det['conf']
            x1, y1, x2, y2 = bbox
            
            # Color based on class
            if class_name == 'pill':
                color = COLOR_YELLOW
            elif class_name == 'pill-on-tongue':
                color = (255, 0, 255)  # Magenta
            elif class_name == 'tongue-no-pill':
                color = COLOR_GREEN
            elif class_name == 'hand':
                color = COLOR_BLUE
            else:
                color = (128, 128, 128)
            
            # Draw box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{class_name}: {conf:.2f}"
            cv2.putText(frame, label, (x1, y1 - 5), FONT, 0.5, color, 2)
        
        # Display status text
        status_y = 30
        cv2.putText(frame, "REAL-TIME PILL DETECTION", (10, status_y), 
                   FONT, 0.7, COLOR_GREEN, 2)
        
        status_y += 30
        if 'pill' in detections:
            cv2.putText(frame, f"✓ PILL DETECTED ({detections['pill']['conf']:.2f})", 
                       (10, status_y), FONT, 0.6, COLOR_GREEN, 2)
        else:
            cv2.putText(frame, "✗ No pill detected", (10, status_y), 
                       FONT, 0.5, (100, 100, 100), 1)
        
        status_y += 25
        if 'hand' in detections:
            cv2.putText(frame, f"✓ HAND DETECTED ({detections['hand']['conf']:.2f})", 
                       (10, status_y), FONT, 0.6, COLOR_GREEN, 2)
        
        status_y += 25
        if 'pill-on-tongue' in detections:
            cv2.putText(frame, f"✓ PILL ON TONGUE ({detections['pill-on-tongue']['conf']:.2f})", 
                       (10, status_y), FONT, 0.6, COLOR_GREEN, 2)
        
        status_y += 25
        if jaw_distance:
            mouth_status = "OPEN" if jaw_distance > 20 else "CLOSED"
            cv2.putText(frame, f"Mouth: {mouth_status} ({jaw_distance:.1f}px)", 
                       (10, status_y), FONT, 0.5, COLOR_YELLOW, 1)
        
        # Show FPS counter
        cv2.putText(frame, "Press 'q' to quit", (10, h - 10), 
                   FONT, 0.5, (200, 200, 200), 1)
        
        # Display frame
        cv2.imshow('Pill Detection - Real-time Test', frame)
        
        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("\n👋 Quitting...")
            break
        elif key == ord('s'):
            print("\n📸 Snapshot taken!")
            print(f"  Detections: {list(detections.keys())}")
            if jaw_distance:
                print(f"  Jaw distance: {jaw_distance:.1f}px")
    
    cap.release()
    cv2.destroyAllWindows()
    print("✅ Test complete!")


if __name__ == "__main__":
    main()
