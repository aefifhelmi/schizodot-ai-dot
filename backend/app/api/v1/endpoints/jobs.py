# app/api/v1/endpoints/jobs.py
"""
Job status and management endpoints
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional
import logging

from schemas.jobs import JobDetail, JobStatusResponse, JobStatus
from repositories.jobs_repository import jobs_repo
from core.validators import validate_job_id, validate_patient_id, validate_pagination_limit
from core.exceptions import job_not_found_exception, internal_server_error_exception

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=list, summary="List all jobs")
async def list_all_jobs(
    limit: int = Query(default=100, ge=1, le=500, description="Maximum number of results")
):
    """
    List all jobs in the system (for clinician dashboard)
    
    Returns all jobs across all patients in reverse chronological order.
    Use this endpoint to populate the clinician dashboard with all patient sessions.
    """
    try:
        limit = validate_pagination_limit(limit, max_limit=500)
        
        result = jobs_repo.list_all_jobs(limit=limit)
        jobs = result.get("items", [])
        
        # Convert to JobDetail models
        job_details = []
        for job in jobs:
            try:
                job_details.append(JobDetail(
                    job_id=job["job_id"],
                    patient_id=job.get("patient_id") or job.get("user_id"),
                    status=JobStatus(job["status"]),
                    s3_key=job["s3_key"],
                    filename=job.get("filename", ""),
                    content_type=job.get("content_type", ""),
                    created_at=job["created_at"],
                    updated_at=job.get("updated_at"),
                    started_at=job.get("started_at"),
                    completed_at=job.get("completed_at"),
                    error=job.get("error"),
                    results=job.get("results")
                ))
            except Exception as e:
                logger.warning(f"Skipping malformed job {job.get('job_id')}: {e}")
                continue
        
        # Sort by created_at descending (most recent first)
        job_details.sort(key=lambda x: x.created_at, reverse=True)
        
        return job_details
        
    except Exception as e:
        logger.error(f"Failed to list all jobs: {str(e)}", exc_info=True)
        raise internal_server_error_exception("retrieve all jobs", str(e))


@router.get("/{job_id}/status", response_model=JobStatusResponse, summary="Get job status")
async def get_job_status(job_id: str):
    """
    Get the current status of an analysis job
    
    Returns:
    - Job status (queued, processing, completed, failed)
    - Progress percentage (if available)
    - Status message
    - Error details (if failed)
    - Whether results are available
    
    Poll this endpoint to track job progress after creating a job.
    """
    try:
        # Validate job ID format
        job_id = validate_job_id(job_id)
        
        job = jobs_repo.get_job(job_id)
        
        if not job:
            raise job_not_found_exception(job_id)
        
        # Determine if results are available
        results_available = (
            job.get("status") == JobStatus.COMPLETED.value and 
            job.get("results") is not None
        )
        
        return JobStatusResponse(
            job_id=job["job_id"],
            status=JobStatus(job["status"]),
            progress=job.get("progress"),
            message=job.get("message"),
            error=job.get("error"),
            created_at=job["created_at"],
            updated_at=job["updated_at"],
            results_available=results_available
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status for {job_id}: {str(e)}", exc_info=True)
        raise internal_server_error_exception("retrieve job status", str(e))


@router.get("/{job_id}", response_model=JobDetail, summary="Get complete job details")
async def get_job_detail(job_id: str):
    """
    Get complete job information including results (if available)
    
    Returns all job fields including:
    - Status and timestamps
    - S3 key and file metadata
    - Error details (if failed)
    - Complete analysis results (if completed)
    """
    try:
        # Validate job ID format
        job_id = validate_job_id(job_id)
        
        job = jobs_repo.get_job(job_id)
        
        if not job:
            raise job_not_found_exception(job_id)
        
        return JobDetail(
            job_id=job["job_id"],
            patient_id=job["patient_id"],
            status=JobStatus(job["status"]),
            s3_key=job["s3_key"],
            filename=job["filename"],
            content_type=job["content_type"],
            created_at=job["created_at"],
            updated_at=job["updated_at"],
            started_at=job.get("started_at"),
            completed_at=job.get("completed_at"),
            error=job.get("error"),
            results=job.get("results")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job details for {job_id}: {str(e)}", exc_info=True)
        raise internal_server_error_exception("retrieve job details", str(e))


@router.get("/patient/{patient_id}", response_model=list, summary="List jobs for patient")
async def list_patient_jobs(
    patient_id: str,
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of results"),
    status_filter: Optional[JobStatus] = Query(default=None, description="Filter by status")
):
    """
    List all jobs for a specific patient
    
    Returns jobs in reverse chronological order (most recent first).
    Supports pagination and status filtering.
    """
    try:
        # Validate inputs
        patient_id = validate_patient_id(patient_id)
        limit = validate_pagination_limit(limit, max_limit=100)
        
        result = jobs_repo.list_jobs_by_patient(
            patient_id=patient_id,
            limit=limit
        )
        
        jobs = result.get("items", [])
        
        # Apply status filter if provided
        if status_filter:
            jobs = [j for j in jobs if j.get("status") == status_filter.value]
        
        # Convert to JobDetail models
        job_details = [
            JobDetail(
                job_id=job["job_id"],
                patient_id=job["patient_id"],
                status=JobStatus(job["status"]),
                s3_key=job["s3_key"],
                filename=job["filename"],
                content_type=job["content_type"],
                created_at=job["created_at"],
                updated_at=job["updated_at"],
                started_at=job.get("started_at"),
                completed_at=job.get("completed_at"),
                error=job.get("error"),
                results=job.get("results")
            )
            for job in jobs
        ]
        
        return job_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list jobs for patient {patient_id}: {str(e)}", exc_info=True)
        raise internal_server_error_exception("retrieve patient jobs", str(e))
