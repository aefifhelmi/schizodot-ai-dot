# app/schemas/jobs.py
"""
Job-related Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Job status enumeration"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobCreate(BaseModel):
    """Request model for creating a new analysis job"""
    patient_id: str = Field(..., min_length=1, max_length=100, description="Patient identifier")
    filename: str = Field(..., min_length=1, max_length=255, description="Original filename")
    content_type: str = Field(..., description="MIME type (e.g., video/mp4, audio/wav)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "patient_id": "patient-001",
                "filename": "checkin-2024-01-15.mp4",
                "content_type": "video/mp4",
                "metadata": {"session_type": "weekly_checkin"}
            }
        }


class JobResponse(BaseModel):
    """Response model after creating a job"""
    job_id: str = Field(..., description="Unique job identifier")
    patient_id: str
    status: JobStatus
    s3_key: str = Field(..., description="S3 object key for the uploaded file")
    presigned_url: str = Field(..., description="Presigned URL for direct S3 upload")
    presigned_url_expires_in: int = Field(default=900, description="URL expiration in seconds")
    created_at: str = Field(..., description="ISO 8601 timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job-abc123",
                "patient_id": "patient-001",
                "status": "queued",
                "s3_key": "uploads/patient-001/20240115T120000Z_checkin.mp4",
                "presigned_url": "https://s3.amazonaws.com/...",
                "presigned_url_expires_in": 900,
                "created_at": "2024-01-15T12:00:00Z"
            }
        }


class JobDetail(BaseModel):
    """Detailed job information"""
    job_id: str
    patient_id: str
    status: JobStatus
    s3_key: str
    filename: str
    content_type: str
    created_at: str
    updated_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    results: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job-abc123",
                "patient_id": "patient-001",
                "status": "completed",
                "s3_key": "uploads/patient-001/20240115T120000Z_checkin.mp4",
                "filename": "checkin-2024-01-15.mp4",
                "content_type": "video/mp4",
                "created_at": "2024-01-15T12:00:00Z",
                "updated_at": "2024-01-15T12:05:30Z",
                "started_at": "2024-01-15T12:01:00Z",
                "completed_at": "2024-01-15T12:05:30Z",
                "error": None,
                "results": {
                    "emotion_summary": "calm",
                    "compliance_score": 0.95
                }
            }
        }


class JobStatusResponse(BaseModel):
    """Response for job status queries"""
    job_id: str
    status: JobStatus
    progress: Optional[int] = Field(None, ge=0, le=100, description="Progress percentage")
    message: Optional[str] = Field(None, description="Human-readable status message")
    error: Optional[str] = None
    created_at: str
    updated_at: str
    results_available: bool = Field(default=False, description="Whether results are ready")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job-abc123",
                "status": "processing",
                "progress": 65,
                "message": "Running emotion detection...",
                "error": None,
                "created_at": "2024-01-15T12:00:00Z",
                "updated_at": "2024-01-15T12:03:00Z",
                "results_available": False
            }
        }
