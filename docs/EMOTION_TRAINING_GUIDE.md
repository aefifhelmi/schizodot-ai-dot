# 🎭 Audio-Visual Emotion Recognition Training Guide

Complete guide to train real emotion recognition models for SchizoDot AI.

## 📋 Overview

We use the **multimodal emotion recognition** system from `external/emotion-av` which implements:
- **Audio emotion recognition** using speech features
- **Visual emotion recognition** using facial expressions
- **Multimodal fusion** combining both modalities
- **8 emotion classes**: neutral, calm, happy, sad, angry, fearful, disgust, surprised

**Dataset:** RAVDESS (Ryerson Audio-Visual Database of Emotional Speech and Song)  
**Training time:** 4-8 hours (with GPU) or 24-48 hours (CPU only)  
**Model accuracy:** ~85% on test set (state-of-the-art)

---

## 🚀 Quick Start

### Option 1: Automated Setup

```bash
cd /Users/tengkuafif/schizodot-ai-dot
chmod +x scripts/setup_emotion_training.sh
./scripts/setup_emotion_training.sh
```

### Option 2: Manual Setup (Detailed Below)

---

## 📥 Step 1: Download RAVDESS Dataset (Required)

### 1.1 Download Links

Go to: **https://zenodo.org/record/1188976**

Download these files:
- ✅ `Video_Speech_Actor_01.zip` through `Video_Speech_Actor_24.zip` (24 files, ~1GB each)
- ✅ `Audio_Speech_Actor_01-24.zip` (1 file, ~500MB)

**Total size:** ~24GB  
**Download time:** 30 minutes - 2 hours (depending on connection)

### 1.2 Extract Dataset

```bash
# Create data directory
mkdir -p /Users/tengkuafif/schizodot-ai-dot/data/RAVDESS

# Extract all zip files to this directory
# After extraction, you should have:
cd /Users/tengkuafif/schizodot-ai-dot/data/RAVDESS
ls

# Expected output:
# Actor_01/  Actor_07/  Actor_13/  Actor_19/
# Actor_02/  Actor_08/  Actor_14/  Actor_20/
# Actor_03/  Actor_09/  Actor_15/  Actor_21/
# Actor_04/  Actor_10/  Actor_16/  Actor_22/
# Actor_05/  Actor_11/  Actor_17/  Actor_23/
# Actor_06/  Actor_12/  Actor_18/  Actor_24/
```

### 1.3 Verify Dataset Structure

```bash
# Check one actor folder
ls /Users/tengkuafif/schizodot-ai-dot/data/RAVDESS/Actor_01/

# Should contain .mp4 and .wav files like:
# 01-01-01-01-01-01-01.mp4
# 01-01-01-01-01-02-01.mp4
# 03-01-01-01-01-01-01.wav
# 03-01-01-01-01-02-01.wav
# etc.
```

---

## 🔧 Step 2: Install Dependencies

```bash
cd /Users/tengkuafif/schizodot-ai-dot/external/emotion-av

# Install core requirements
pip install torch==1.9.0 torchvision==0.10.0
pip install librosa==0.8.1
pip install opencv-python tqdm

# Install face detection
pip install facenet-pytorch

# Verify installation
python -c "import torch; import librosa; import cv2; print('✅ All dependencies installed')"
```

---

## 🎬 Step 3: Preprocess Dataset

### 3.1 Update Paths in Scripts

```bash
cd /Users/tengkuafif/schizodot-ai-dot/external/emotion-av/ravdess_preprocessing

# Edit extract_faces.py - change line 21:
# FROM: root = '/lustre/scratch/chumache/RAVDESS_or/'
# TO:   root = '/Users/tengkuafif/schizodot-ai-dot/data/RAVDESS'

# Edit extract_audios.py - change the root path similarly

# Edit create_annotations.py - change the root path similarly
```

Or use sed to update automatically:

```bash
DATA_DIR="/Users/tengkuafif/schizodot-ai-dot/data/RAVDESS"
PREPROCESS_DIR="/Users/tengkuafif/schizodot-ai-dot/external/emotion-av/ravdess_preprocessing"

sed -i.bak "s|root = '.*'|root = '$DATA_DIR'|g" "$PREPROCESS_DIR/extract_faces.py"
sed -i.bak "s|root = '.*'|root = '$DATA_DIR'|g" "$PREPROCESS_DIR/extract_audios.py"
sed -i.bak "s|root = '.*'|root = '$DATA_DIR'|g" "$PREPROCESS_DIR/create_annotations.py"
```

### 3.2 Extract Faces from Videos

```bash
cd /Users/tengkuafif/schizodot-ai-dot/external/emotion-av/ravdess_preprocessing

python extract_faces.py
```

**Time:** ~30-60 minutes  
**Output:** Face crops saved as numpy arrays in each Actor folder

### 3.3 Extract Audio Features

```bash
python extract_audios.py
```

**Time:** ~15-30 minutes  
**Output:** Audio files processed and saved

### 3.4 Create Annotations File

```bash
python create_annotations.py
```

**Output:** `annotations.txt` file in RAVDESS directory

Verify:
```bash
head -5 /Users/tengkuafif/schizodot-ai-dot/data/RAVDESS/annotations.txt

# Should show paths to processed data
```

---

## 🏋️ Step 4: Train the Model

### 4.1 (Optional) Download Pretrained Weights

For better performance, download EfficientFace pretrained on AffectNet:

```bash
cd /Users/tengkuafif/schizodot-ai-dot/external/emotion-av
mkdir -p pretrained

# Download pretrained model
wget https://github.com/zengqunzhao/EfficientFace/releases/download/v1.0/EfficientFace_Trained_on_AffectNet7.pth.tar \
  -O pretrained/EfficientFace_Trained_on_AffectNet7.pth.tar
```

### 4.2 Start Training

```bash
cd /Users/tengkuafif/schizodot-ai-dot/external/emotion-av

# Create results directory
mkdir -p /Users/tengkuafif/schizodot-ai-dot/models/emotion

# Train with intermediate attention fusion (best performance)
python main.py \
  --fusion ia \
  --mask softhard \
  --annotation_path /Users/tengkuafif/schizodot-ai-dot/data/RAVDESS/annotations.txt \
  --result_path /Users/tengkuafif/schizodot-ai-dot/models/emotion \
  --pretrain_path pretrained/EfficientFace_Trained_on_AffectNet7.pth.tar \
  --n_epochs 100 \
  --batch_size 16
```

**Training time:**
- With GPU (CUDA): 4-8 hours
- CPU only: 24-48 hours

**Expected accuracy:** ~85% on test set

### 4.3 Monitor Training

Training will output:
- Validation accuracy every epoch
- Best model saved automatically
- Test results in `models/emotion/test_set_bestval.txt`

---

## 💾 Step 5: Export Trained Model

After training completes:

```bash
# Find the best checkpoint
ls /Users/tengkuafif/schizodot-ai-dot/models/emotion/

# Should see: save_best.pth

# Copy to emotion demo weights
cp /Users/tengkuafif/schizodot-ai-dot/models/emotion/save_best.pth \
   /Users/tengkuafif/schizodot-ai-dot/schizodot_emotion_demo/ai/emotion/weights/av_emotion_best.pth
```

---

## 🔌 Step 6: Update Emotion Service to Use Trained Model

Now update the emotion service to use the real trained model instead of stubs.

### 6.1 Create Model Wrapper

Create: `/Users/tengkuafif/schizodot-ai-dot/schizodot_emotion_demo/backend/services/emotion/av_infer.py`

```python
"""Wrapper for trained audiovisual emotion model"""
import sys
import torch
from pathlib import Path

# Add external/emotion-av to path
emotion_av_path = Path(__file__).resolve().parents[5] / "external" / "emotion-av"
sys.path.insert(0, str(emotion_av_path))

from models.model import generate_model
from opts import parse_opts

class AVEmotionModel:
    """Trained audiovisual emotion recognition model"""
    
    def __init__(self, checkpoint_path=None):
        if checkpoint_path is None:
            root = Path(__file__).resolve().parents[3]
            checkpoint_path = root / "ai/emotion/weights/av_emotion_best.pth"
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load model
        opt = parse_opts()
        opt.fusion = 'ia'  # intermediate attention
        opt.n_classes = 8
        
        self.model = generate_model(opt)
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        self.model.load_state_dict(checkpoint['state_dict'])
        self.model.to(self.device)
        self.model.eval()
        
        self.emotions = ['neutral', 'calm', 'happy', 'sad', 'angry', 'fearful', 'disgust', 'surprised']
    
    def predict(self, video_path: str):
        """Predict emotion from video"""
        # Preprocessing and inference logic here
        # Returns: {"label": "happy", "probs": {...}}
        pass
```

### 6.2 Update API to Use Real Model

Update `/Users/tengkuafif/schizodot-ai-dot/schizodot_emotion_demo/backend/services/emotion/api.py`:

```python
from backend.services.emotion.av_infer import AVEmotionModel

# Use trained model instead of separate audio/face models
av_model = AVEmotionModel()

@router.post("/emotion/predict")
async def predict_emotion(file: UploadFile = File(...)):
    # ... existing code ...
    result = av_model.predict(tmp_path)
    return result
```

---

## 🧪 Step 7: Test Trained Model

```bash
cd /Users/tengkuafif/schizodot-ai-dot/schizodot_emotion_demo

# Start service
export PYTHONPATH=$(pwd)
uvicorn backend.main:app --port 8001 --reload

# Test with sample video
curl -X POST http://localhost:8001/v1/emotion/predict \
  -F "file=@test_video.mp4" \
  | python3 -m json.tool
```

**Expected output:**
```json
{
  "emotion": "happy",
  "confidence": 0.87,
  "all_emotions": {
    "neutral": 0.02,
    "calm": 0.03,
    "happy": 0.87,
    "sad": 0.01,
    "angry": 0.01,
    "fearful": 0.02,
    "disgust": 0.01,
    "surprised": 0.03
  },
  "model": "trained_av_fusion"
}
```

---

## 📊 Alternative: Use Pretrained Models

If you don't want to train from scratch, download pretrained models:

```bash
# Download from the paper's shared models
# https://tuni-my.sharepoint.com/:f:/g/personal/kateryna_chumachenko_tuni_fi/EvPvmdroOg1Hgtsvxo6N9yMBgC9nHjo-V1FVHwzcf8FTqw?e=188a8U

# Extract and place in:
mkdir -p /Users/tengkuafif/schizodot-ai-dot/models/emotion
# Copy the .pth file there
```

---

## ✅ Success Checklist

- [ ] RAVDESS dataset downloaded (24GB)
- [ ] Dataset extracted to correct location
- [ ] Dependencies installed
- [ ] Faces extracted from videos
- [ ] Audio features extracted
- [ ] Annotations file created
- [ ] Model trained (or pretrained downloaded)
- [ ] Model integrated into emotion service
- [ ] Service tested with real predictions

---

## 🚨 Troubleshooting

### Issue: "CUDA out of memory"
**Solution:** Reduce batch size: `--batch_size 8` or `--batch_size 4`

### Issue: "No module named 'facenet_pytorch'"
**Solution:** `pip install facenet-pytorch`

### Issue: Training is very slow
**Solution:** 
- Use GPU if available
- Reduce `--n_epochs` to 50 for faster training
- Use pretrained model instead

### Issue: "annotations.txt not found"
**Solution:** Make sure preprocessing step 3 completed successfully

---

## 📈 Expected Performance

| Metric | Value |
|--------|-------|
| Test Accuracy | ~85% |
| Training Time (GPU) | 4-8 hours |
| Training Time (CPU) | 24-48 hours |
| Model Size | ~50MB |
| Inference Time | ~100ms per video |

---

## 🎯 Next Steps

After training is complete:
1. ✅ Integrate trained model into emotion service
2. ✅ Update main backend to call emotion service
3. ✅ Test end-to-end pipeline
4. ✅ Proceed with Phase 4 (Bedrock LLM integration)

---

**Training Status:** Ready to start  
**Estimated Total Time:** 1-2 days (including download and preprocessing)
