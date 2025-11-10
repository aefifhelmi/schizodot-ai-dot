# app/worker/tasks.py
"""
Celery tasks for background processing
Handles AI analysis pipeline orchestration
"""
import os
import tempfile
import logging
from typing import Dict, Any
from datetime import datetime, timezone

import requests
from celery import Task
from app.worker import celery_app
from app.core.aws import s3, dynamodb
from app.core.config import settings

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """Base task with callbacks for success/failure"""
    
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Task {task_id} succeeded with result: {retval}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {task_id} failed: {exc}")


@celery_app.task(bind=True, base=CallbackTask, max_retries=3)
def analyze_media(self, job_id: str, patient_id: str, s3_key: str) -> Dict[str, Any]:
    """
    Main orchestration task for media analysis
    
    Args:
        job_id: Unique job identifier
        patient_id: Patient identifier
        s3_key: S3 object key for the media file
    
    Returns:
        Dict containing analysis results
    """
    try:
        logger.info(f"Starting analysis for job {job_id}")
        
        # Step 1: Update job status to "processing"
        update_job_status(job_id, "processing")
        
        # Step 2: Download file from S3
        logger.info(f"Downloading file from S3: {s3_key}")
        local_path = download_from_s3(s3_key)
        
        # Step 3: Run emotion detection
        logger.info("Running emotion detection...")
        emotion_result = call_emotion_service(local_path)
        
        # Step 4: Run object detection (pill verification)
        logger.info("Running object detection...")
        object_result = call_object_detection_service(local_path)
        
        # Step 5: Multimodal fusion
        logger.info("Performing multimodal fusion...")
        fusion_result = multimodal_fusion(emotion_result, object_result)
        
        # Step 6: LLM analysis (if Bedrock enabled)
        clinical_summary = None
        if settings.BEDROCK_ENABLE:
            logger.info("Generating clinical summary with Bedrock...")
            clinical_summary = bedrock_analysis(fusion_result)
        else:
            logger.info("Bedrock disabled, using rule-based summary")
            clinical_summary = rule_based_summary(fusion_result)
        
        # Step 7: Store results in DynamoDB
        results = {
            "job_id": job_id,
            "patient_id": patient_id,
            "s3_key": s3_key,
            "emotion_analysis": emotion_result,
            "object_detection": object_result,
            "fusion_result": fusion_result,
            "clinical_summary": clinical_summary,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "status": "completed"
        }
        
        store_results(job_id, results)
        
        # Step 8: Update job status to "completed"
        update_job_status(job_id, "completed", results=results)
        
        # Cleanup
        if os.path.exists(local_path):
            os.remove(local_path)
        
        logger.info(f"Analysis completed for job {job_id}")
        return results
        
    except Exception as e:
        logger.error(f"Analysis failed for job {job_id}: {str(e)}")
        update_job_status(job_id, "failed", error=str(e))
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


def download_from_s3(s3_key: str) -> str:
    """Download file from S3 to temporary location"""
    try:
        s3_client = s3()
        
        # Create temporary file
        suffix = os.path.splitext(s3_key)[1] or ".mp4"
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp_path = tmp_file.name
        tmp_file.close()
        
        # Download from S3
        s3_client.download_file(
            Bucket=settings.S3_BUCKET,
            Key=s3_key,
            Filename=tmp_path
        )
        
        logger.info(f"Downloaded {s3_key} to {tmp_path}")
        return tmp_path
        
    except Exception as e:
        logger.error(f"Failed to download from S3: {e}")
        raise


def call_emotion_service(file_path: str) -> Dict[str, Any]:
    """Call AI pipeline emotion detection service"""
    try:
        ai_url = os.getenv("AI_PIPELINE_URL", "http://ai-pipeline:8001")
        
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(
                f"{ai_url}/emotion/analyze",
                files=files,
                timeout=120
            )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"Emotion service returned {response.status_code}")
            return {"error": "emotion_service_failed", "status": "failed"}
            
    except Exception as e:
        logger.error(f"Failed to call emotion service: {e}")
        return {"error": str(e), "status": "failed"}


def call_object_detection_service(file_path: str) -> Dict[str, Any]:
    """Call AI pipeline object detection service"""
    try:
        ai_url = os.getenv("AI_PIPELINE_URL", "http://ai-pipeline:8001")
        
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(
                f"{ai_url}/object-detection/analyze",
                files=files,
                timeout=120
            )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"Object detection service returned {response.status_code}")
            return {"error": "object_detection_failed", "status": "mock"}
            
    except Exception as e:
        logger.error(f"Failed to call object detection service: {e}")
        return {"error": str(e), "status": "failed"}


def multimodal_fusion(emotion_result: Dict, object_result: Dict) -> Dict[str, Any]:
    """Combine emotion and object detection results"""
    return {
        "patient_state": {
            "audio_emotion": emotion_result.get("audio_emotion", {}),
            "facial_emotion": emotion_result.get("face_emotion", {}),
            "emotional_consistency": calculate_consistency(emotion_result)
        },
        "medication_compliance": {
            "pill_detected": object_result.get("pill_detected", False),
            "compliance_score": object_result.get("confidence", 0.0),
            "verification_status": object_result.get("compliance", False)
        },
        "risk_level": assess_risk(emotion_result, object_result),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def calculate_consistency(emotion_result: Dict) -> str:
    """Calculate consistency between audio and facial emotions"""
    # Placeholder logic
    return "consistent"


def assess_risk(emotion_result: Dict, object_result: Dict) -> str:
    """Assess patient risk level based on analysis"""
    # Placeholder logic - to be enhanced
    if not object_result.get("compliance", True):
        return "high"
    return "low"


def bedrock_analysis(fusion_result: Dict) -> Dict[str, Any]:
    """Generate clinical summary using AWS Bedrock"""
    # TODO: Implement Bedrock integration
    logger.info("Bedrock analysis called (not yet implemented)")
    return rule_based_summary(fusion_result)


def rule_based_summary(fusion_result: Dict) -> Dict[str, Any]:
    """Generate rule-based clinical summary"""
    patient_state = fusion_result.get("patient_state", {})
    compliance = fusion_result.get("medication_compliance", {})
    
    summary = {
        "emotional_state": "Appears calm and stable",
        "medication_adherence": "Compliant" if compliance.get("compliance_score", 0) > 0.7 else "Non-compliant",
        "risk_assessment": fusion_result.get("risk_level", "low"),
        "recommendations": [
            "Continue monitoring",
            "Schedule follow-up if needed"
        ],
        "generated_by": "rule_based_system",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    return summary


def update_job_status(job_id: str, status: str, **kwargs):
    """Update job status in DynamoDB"""
    try:
        table = dynamodb().Table(settings.DYNAMO_TABLE_JOBS)
        
        update_expr = "SET #status = :status, updated_at = :updated_at"
        expr_values = {
            ":status": status,
            ":updated_at": datetime.now(timezone.utc).isoformat()
        }
        expr_names = {"#status": "status"}
        
        # Add optional fields
        if "results" in kwargs:
            update_expr += ", results = :results"
            expr_values[":results"] = kwargs["results"]
        
        if "error" in kwargs:
            update_expr += ", error = :error"
            expr_values[":error"] = kwargs["error"]
        
        table.update_item(
            Key={"job_id": job_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values
        )
        
        logger.info(f"Updated job {job_id} status to {status}")
        
    except Exception as e:
        logger.error(f"Failed to update job status: {e}")


def store_results(job_id: str, results: Dict[str, Any]):
    """Store analysis results in DynamoDB"""
    try:
        table = dynamodb().Table(settings.DYNAMO_TABLE)
        
        item = {
            "user_id": results["patient_id"],
            "timestamp": results["analyzed_at"],
            "job_id": job_id,
            "s3_key": results["s3_key"],
            "analysis_type": "multimodal",
            "results": results,
            "status": "completed"
        }
        
        table.put_item(Item=item)
        logger.info(f"Stored results for job {job_id}")
        
    except Exception as e:
        logger.error(f"Failed to store results: {e}")
        raise
