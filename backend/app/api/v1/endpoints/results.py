# app/api/v1/endpoints/results.py
"""
Analysis results endpoints
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional
import logging

from schemas.results import AnalysisResult, PatientResultsList
from repositories.results_repository import results_repo
from core.validators import validate_patient_id, validate_job_id, validate_pagination_limit
from core.exceptions import result_not_found_exception, internal_server_error_exception

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{patient_id}", response_model=PatientResultsList, summary="Get patient analysis results")
async def get_patient_results(
    patient_id: str,
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of results"),
    next_token: Optional[str] = Query(default=None, description="Pagination token")
):
    """
    Get analysis results for a specific patient
    
    Returns the most recent analysis results in reverse chronological order.
    Supports pagination for patients with many results.
    
    Each result includes:
    - Audio emotion analysis
    - Facial emotion analysis
    - Medication compliance detection
    - Multimodal fusion
    - Clinical summary and recommendations
    """
    try:
        # Validate inputs
        patient_id = validate_patient_id(patient_id)
        limit = validate_pagination_limit(limit, max_limit=50)
        
        # Parse pagination token if provided
        last_evaluated_key = None
        if next_token:
            try:
                import json
                import base64
                last_evaluated_key = json.loads(base64.b64decode(next_token))
            except Exception as e:
                logger.warning(f"Invalid pagination token: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid pagination token"
                )
        
        # Get results from repository
        result = results_repo.get_latest_results(
            patient_id=patient_id,
            limit=limit,
            last_evaluated_key=last_evaluated_key
        )
        
        items = result.get("items", [])
        next_key = result.get("next_token")
        
        # Convert to AnalysisResult models
        analysis_results = []
        for item in items:
            results_data = item.get("results", {})
            
            analysis_results.append(AnalysisResult(
                job_id=item.get("job_id"),
                patient_id=item.get("user_id"),
                s3_key=item.get("s3_key"),
                analyzed_at=item.get("analyzed_at"),
                audio_emotion=results_data.get("audio_emotion"),
                facial_emotion=results_data.get("facial_emotion"),
                compliance=results_data.get("compliance"),
                multimodal_fusion=results_data.get("multimodal_fusion"),
                clinical_summary=results_data.get("clinical_summary"),
                processing_time_seconds=item.get("processing_time_seconds")
            ))
        
        # Encode next token if available
        encoded_next_token = None
        if next_key:
            import json
            import base64
            encoded_next_token = base64.b64encode(
                json.dumps(next_key).encode()
            ).decode()
        
        # Get total count
        total_results = results_repo.count_results_for_patient(patient_id)
        
        return PatientResultsList(
            patient_id=patient_id,
            total_results=total_results,
            results=analysis_results,
            next_token=encoded_next_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get results for patient {patient_id}: {str(e)}", exc_info=True)
        raise internal_server_error_exception("retrieve patient results", str(e))


@router.get("/job/{job_id}", response_model=AnalysisResult, summary="Get result by job ID")
async def get_result_by_job(job_id: str):
    """
    Get analysis result for a specific job
    
    Returns the complete analysis result if the job has completed successfully.
    Returns 404 if the job hasn't completed or no result exists.
    """
    try:
        # Validate job ID format
        job_id = validate_job_id(job_id)
        
        item = results_repo.get_result_by_job(job_id)
        
        if not item:
            raise result_not_found_exception(job_id, "job")
        
        results_data = item.get("results", {})
        
        return AnalysisResult(
            job_id=item.get("job_id"),
            patient_id=item.get("user_id"),
            s3_key=item.get("s3_key"),
            analyzed_at=item.get("analyzed_at"),
            audio_emotion=results_data.get("audio_emotion"),
            facial_emotion=results_data.get("facial_emotion"),
            compliance=results_data.get("compliance"),
            multimodal_fusion=results_data.get("multimodal_fusion"),
            clinical_summary=results_data.get("clinical_summary"),
            processing_time_seconds=item.get("processing_time_seconds")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get result for job {job_id}: {str(e)}", exc_info=True)
        raise internal_server_error_exception("retrieve job result", str(e))
