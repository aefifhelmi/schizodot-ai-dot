# app/api/v1/endpoints/analyze.py
"""
Analysis endpoints for job creation and media upload
"""
from fastapi import APIRouter, HTTPException, status
from typing import List
import logging

from schemas.jobs import JobCreate, JobResponse, JobStatus
from repositories.jobs_repository import jobs_repo
from services.presign_service import create_presigned_put_url, object_key
from worker import celery_app
from core.validators import (
    validate_patient_id,
    validate_filename,
    validate_content_type,
    sanitize_metadata,
    ALLOWED_CONTENT_TYPES
)
from core.exceptions import (
    internal_server_error_exception,
    DynamoDBException,
    S3Exception
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED, summary="Create analysis job")
async def create_analysis_job(request: JobCreate):
    """
    Create a new analysis job and return presigned S3 upload URL
    
    This endpoint:
    1. Validates the request (content type, patient ID, filename)
    2. Creates a job record in DynamoDB with status 'queued'
    3. Generates a presigned S3 URL for direct upload
    4. Enqueues a Celery task for background processing
    5. Returns job details including the upload URL
    
    The client should:
    1. Call this endpoint to get upload URL
    2. Upload file directly to S3 using the presigned URL
    3. Poll /jobs/{job_id}/status to track progress
    """
    try:
        # Validate inputs
        patient_id = validate_patient_id(request.patient_id)
        filename = validate_filename(request.filename)
        content_type = validate_content_type(request.content_type)
        metadata = sanitize_metadata(request.metadata)
        
        # Generate S3 key
        s3_key = object_key(patient_id, filename)
        
        # Create job record in DynamoDB
        job = jobs_repo.create_job(
            patient_id=patient_id,
            s3_key=s3_key,
            filename=filename,
            content_type=content_type,
            metadata=metadata
        )
        
        logger.info(f"Created job {job['job_id']} for patient {request.patient_id}")
        
        # Generate presigned URL for upload
        presigned_data = create_presigned_put_url(
            key=s3_key,
            content_type=content_type,
            expires_seconds=900  # 15 minutes
        )
        
        # Enqueue Celery task for background processing
        # Task will be picked up after the file is uploaded
        celery_app.send_task(
            "worker.tasks.analyze_media",
            args=[job["job_id"], patient_id, s3_key],
            countdown=60  # Wait 60 seconds for upload to complete
        )
        
        logger.info(f"Enqueued analysis task for job {job['job_id']}")
        
        # Return response
        return JobResponse(
            job_id=job["job_id"],
            patient_id=job["patient_id"],
            status=JobStatus(job["status"]),
            s3_key=s3_key,
            presigned_url=presigned_data["url"],
            presigned_url_expires_in=900,
            created_at=job["created_at"]
        )
        
    except HTTPException:
        # Re-raise validation and other HTTP exceptions
        raise
    except DynamoDBException as e:
        logger.error(f"DynamoDB error creating job: {str(e)}")
        raise internal_server_error_exception("create job in database", str(e))
    except S3Exception as e:
        logger.error(f"S3 error generating presigned URL: {str(e)}")
        raise internal_server_error_exception("generate upload URL", str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating analysis job: {str(e)}", exc_info=True)
        raise internal_server_error_exception("create analysis job", str(e))
