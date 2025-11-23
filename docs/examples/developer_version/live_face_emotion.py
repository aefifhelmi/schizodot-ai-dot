# live_face_emotion.py
#
# Live webcam face emotion demo using FER.
# Press 'q' to quit the window.

import cv2
from fer import FER

def main():
    # Initialize FER detector (mtcnn=True is more accurate but slower)
    detector = FER(mtcnn=True)

    # Open default webcam (0). If you have multiple cameras, you may try 1, 2, ...
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: cannot open webcam")
        return

    frame_count = 0
    current_label = None
    current_probs = {}

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: cannot read frame from webcam")
            break

        frame_count += 1

        # Run emotion detection every N frames to keep it responsive
        if frame_count % 5 == 0:
            results = detector.detect_emotions(frame)
            if results:
                # Take the first detected face
                emotions = results[0]["emotions"]
                # Get dominant emotion
                current_label = max(emotions, key=emotions.get)
                current_probs = emotions
            else:
                current_label = None
                current_probs = {}

        # Draw label on the frame
        display_text = "No face" if current_label is None else f"Emotion: {current_label}"
        cv2.putText(
            frame,
            display_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

        # Show the frame
        cv2.imshow("Live Face Emotion (press 'q' to quit)", frame)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
