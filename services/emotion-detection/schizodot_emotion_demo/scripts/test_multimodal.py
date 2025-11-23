#!/usr/bin/env python3
"""
Test multimodal emotion recognition
Works with or without pretrained model

Usage:
  cd /Users/tengkuafif/schizodot-ai-dot/schizodot_emotion_demo
  source venv/bin/activate
  python scripts/test_multimodal.py
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Check dependencies
try:
    import torch
    import cv2
    import librosa
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("\nPlease install requirements:")
    print("  cd /Users/tengkuafif/schizodot-ai-dot/schizodot_emotion_demo")
    print("  source venv/bin/activate")
    print("  pip install -r backend/services/emotion/requirements.txt")
    sys.exit(1)

from backend.services.emotion.multimodal_infer import MultimodalEmotionModel
import json

def test_multimodal():
    """Test multimodal emotion model"""
    print("🎭 Testing Multimodal Emotion Recognition")
    print("=" * 50)
    
    # Initialize model
    print("\n1. Initializing model...")
    model = MultimodalEmotionModel()
    
    # Check model type
    if model.use_pretrained:
        print("   ✅ Using PRETRAINED multimodal model")
    else:
        print("   ⚠️  Using FER FALLBACK mode")
        print("   (Download pretrained model for full multimodal)")
    
    # Test with sample video
    video_path = Path(__file__).resolve().parents[1] / "test_video.mp4"
    
    if not video_path.exists():
        print(f"\n❌ Test video not found: {video_path}")
        print("   Please ensure test_video.mp4 exists in schizodot_emotion_demo/")
        return
    
    print(f"\n2. Testing with: {video_path.name}")
    
    try:
        result = model.predict_from_video(str(video_path))
        
        print("\n3. Results:")
        print("-" * 50)
        print(json.dumps(result, indent=2))
        print("-" * 50)
        
        # Verify structure
        assert "audio" in result, "Missing audio results"
        assert "face" in result, "Missing face results"
        assert "multimodal" in result, "Missing multimodal results"
        assert "model_type" in result, "Missing model_type"
        
        print("\n✅ Test PASSED!")
        print(f"\nModel Type: {result['model_type']}")
        print(f"Multimodal Prediction: {result['multimodal']['label']}")
        print(f"Confidence: {result['multimodal']['confidence']:.2%}")
        
        if result['model_type'] == 'fer_fallback':
            print("\n💡 To use pretrained model:")
            print("   1. Download from: https://tuni-my.sharepoint.com/:f:/g/personal/kateryna_chumachenko_tuni_fi/EvPvmdroOg1Hgtsvxo6N9yMBgC9nHjo-V1FVHwzcf8FTqw?e=188a8U")
            print("   2. Save as: ai/emotion/weights/av_emotion_best.pth")
            print("   3. Restart the service")
        
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 50)
    print("🎉 Multimodal emotion recognition is working!")

if __name__ == "__main__":
    test_multimodal()
