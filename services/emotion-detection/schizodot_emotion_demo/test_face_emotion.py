# test_face_emotion.py

from backend.services.emotion.face_infer import FaceEmotionModel

if __name__ == "__main__":
    model = FaceEmotionModel()

    # Use one of your RAVDESS mp4 files here
    # Example relative path below; adjust to your actual video location.
    video_path = "test_video.mp4"


    result = model.predict_from_video(video_path, step=5)
    print(result)
