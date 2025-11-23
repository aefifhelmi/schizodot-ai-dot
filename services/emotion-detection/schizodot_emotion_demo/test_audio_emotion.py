from backend.services.emotion.audio_infer import AudioEmotionModel

model = AudioEmotionModel()
out = model.predict_from_path("test_audio.wav")  # replace with your .wav path
print(out)
