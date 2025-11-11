# app/schemas/results.py
"""
Analysis result Pydantic models
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime


class EmotionScore(BaseModel):
    """Emotion detection scores"""
    emotion: str = Field(..., description="Detected emotion (e.g., happy, sad, neutral)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")


class AudioEmotionResult(BaseModel):
    """Audio-based emotion analysis"""
    primary_emotion: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    all_emotions: List[EmotionScore] = Field(default_factory=list)
    audio_quality: Optional[str] = Field(None, description="Audio quality assessment")


class FacialEmotionResult(BaseModel):
    """Face-based emotion analysis"""
    primary_emotion: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    all_emotions: List[EmotionScore] = Field(default_factory=list)
    face_detected: bool = Field(default=True)
    frame_count: Optional[int] = Field(None, description="Number of frames analyzed")


class ComplianceResult(BaseModel):
    """Medication compliance detection"""
    pill_detected: bool
    hand_detected: bool
    face_detected: bool
    compliance_score: float = Field(..., ge=0.0, le=1.0, description="Overall compliance score")
    confidence: float = Field(..., ge=0.0, le=1.0)
    verification_status: str = Field(..., description="compliant, non-compliant, uncertain")


class MultimodalFusion(BaseModel):
    """Combined analysis from multiple modalities"""
    emotional_consistency: str = Field(..., description="Consistency between audio and facial emotions")
    overall_emotion: str = Field(..., description="Fused emotion assessment")
    confidence: float = Field(..., ge=0.0, le=1.0)
    risk_level: str = Field(..., description="low, medium, high")
    risk_factors: List[str] = Field(default_factory=list)


class ClinicalSummary(BaseModel):
    """Clinical summary and recommendations"""
    emotional_state: str = Field(..., description="Overall emotional state description")
    medication_adherence: str = Field(..., description="Adherence status")
    risk_assessment: str = Field(..., description="Risk level assessment")
    recommendations: List[str] = Field(default_factory=list)
    generated_by: str = Field(default="rule_based", description="Summary generation method")
    timestamp: str


class AnalysisResult(BaseModel):
    """Complete analysis result"""
    job_id: str
    patient_id: str
    s3_key: str
    analyzed_at: str
    audio_emotion: Optional[AudioEmotionResult] = None
    facial_emotion: Optional[FacialEmotionResult] = None
    compliance: Optional[ComplianceResult] = None
    multimodal_fusion: Optional[MultimodalFusion] = None
    clinical_summary: Optional[ClinicalSummary] = None
    processing_time_seconds: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job-abc123",
                "patient_id": "patient-001",
                "s3_key": "uploads/patient-001/20240115T120000Z_checkin.mp4",
                "analyzed_at": "2024-01-15T12:05:30Z",
                "audio_emotion": {
                    "primary_emotion": "calm",
                    "confidence": 0.87,
                    "all_emotions": [
                        {"emotion": "calm", "confidence": 0.87},
                        {"emotion": "neutral", "confidence": 0.10}
                    ]
                },
                "facial_emotion": {
                    "primary_emotion": "neutral",
                    "confidence": 0.82,
                    "all_emotions": [
                        {"emotion": "neutral", "confidence": 0.82},
                        {"emotion": "calm", "confidence": 0.15}
                    ],
                    "face_detected": True,
                    "frame_count": 150
                },
                "compliance": {
                    "pill_detected": True,
                    "hand_detected": True,
                    "face_detected": True,
                    "compliance_score": 0.95,
                    "confidence": 0.90,
                    "verification_status": "compliant"
                },
                "multimodal_fusion": {
                    "emotional_consistency": "consistent",
                    "overall_emotion": "calm",
                    "confidence": 0.85,
                    "risk_level": "low",
                    "risk_factors": []
                },
                "clinical_summary": {
                    "emotional_state": "Patient appears calm and stable",
                    "medication_adherence": "Compliant - medication taken as prescribed",
                    "risk_assessment": "Low risk - no concerning indicators",
                    "recommendations": [
                        "Continue current treatment plan",
                        "Schedule routine follow-up"
                    ],
                    "generated_by": "rule_based",
                    "timestamp": "2024-01-15T12:05:30Z"
                },
                "processing_time_seconds": 45.2
            }
        }


class PatientResultsList(BaseModel):
    """List of results for a patient"""
    patient_id: str
    total_results: int
    results: List[AnalysisResult]
    next_token: Optional[str] = Field(None, description="Pagination token for next page")

    class Config:
        json_schema_extra = {
            "example": {
                "patient_id": "patient-001",
                "total_results": 15,
                "results": [],
                "next_token": None
            }
        }
