
# Emotion module integration scaffold

Files here are ready to be copied into your private repo.


- `ai/emotion/notebooks/train_av_emotion_colab.ipynb`: Colab training scaffold.

- `backend/services/emotion/infer.py`: Wrapper with a stable API. Wire to upstream model and transforms.

- `backend/services/emotion/api.py`: FastAPI route `/v1/emotion/predict` that accepts a video upload.

- `backend/main.py`: FastAPI app mounting the route.

- `backend/services/emotion/requirements.txt`: Python runtime deps for inference.

- `infra/docker/emotion.Dockerfile`: Runtime container with ffmpeg and PyTorch.

- `.gitattributes`: Git LFS rules for model weights.

- `.gitignore`: Ignore datasets and caches.

- `THIRD_PARTY_NOTICES.md`: Upstream attribution.

