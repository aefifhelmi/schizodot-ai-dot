# app/schemas/__init__.py
"""
Pydantic schemas for request/response validation
"""
from schemas.jobs import (
    JobStatus,
    JobCreate,
    JobResponse,
    JobDetail,
    JobStatusResponse
)
from schemas.results import (
    EmotionScore,
    AudioEmotionResult,
    FacialEmotionResult,
    ComplianceResult,
    MultimodalFusion,
    ClinicalSummary,
    AnalysisResult,
    PatientResultsList
)

__all__ = [
    # Job schemas
    "JobStatus",
    "JobCreate",
    "JobResponse",
    "JobDetail",
    "JobStatusResponse",
    # Result schemas
    "EmotionScore",
    "AudioEmotionResult",
    "FacialEmotionResult",
    "ComplianceResult",
    "MultimodalFusion",
    "ClinicalSummary",
    "AnalysisResult",
    "PatientResultsList",
]
