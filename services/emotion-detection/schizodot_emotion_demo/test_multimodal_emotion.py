# test_multimodal_emotion.py

from backend.services.emotion.emotion_service import EmotionService

if __name__ == "__main__":
    svc = EmotionService()

    # Set correct paths for your test files
    audio_path = "test_audio.wav"
    video_path = "test_video.mp4"

    result = svc.analyze(audio_path=audio_path, video_path=video_path)
    print(result)
