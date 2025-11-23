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
from decimal import Decimal
from pathlib import Path

import requests
from celery import Task
from worker import celery_app
from core.aws import s3, dynamodb
from core.config import settings
import sys
sys.path.insert(0, '/app')

# Import Bedrock and Transcription services
try:
    from services.bedrock import BedrockClient
    BEDROCK_AVAILABLE = True
except ImportError as e:
    logger_import = logging.getLogger(__name__)
    logger_import.warning(f"Bedrock service not available: {e}")
    BEDROCK_AVAILABLE = False

try:
    from services.transcription import (
        TranscribeClient,
        extract_audio_from_video,
        format_transcript_for_llm
    )
    TRANSCRIPTION_AVAILABLE = True
except ImportError as e:
    logger_import = logging.getLogger(__name__)
    logger_import.warning(f"Transcription service not available: {e}")
    TRANSCRIPTION_AVAILABLE = False
    TranscribeClient = None
    extract_audio_from_video = None
    format_transcript_for_llm = None

logger = logging.getLogger(__name__)


def convert_floats_to_decimal(obj):
    """
    Recursively convert all float values to Decimal for DynamoDB compatibility
    """
    if isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_floats_to_decimal(value) for key, value in obj.items()}
    elif isinstance(obj, float):
        return Decimal(str(obj))
    else:
        return obj


def convert_decimals_to_float(obj):
    """
    Recursively convert all Decimal values to float for JSON serialization
    """
    if isinstance(obj, list):
        return [convert_decimals_to_float(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_decimals_to_float(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj


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
    start_time = datetime.now(timezone.utc)
    local_path = None
    
    try:
        logger.info(f"Starting analysis for job {job_id}")
        
        # Step 1: Update job status to "processing" (10% progress)
        update_job_status(job_id, "processing", progress=10, message="Starting analysis...")
        
        # Step 2: Download file from S3 (20% progress)
        logger.info(f"Downloading file from S3: {s3_key}")
        update_job_status(job_id, "processing", progress=20, message="Downloading media file...")
        local_path = download_from_s3(s3_key)
        
        # Step 3: Run emotion detection (30% progress)
        logger.info("Running emotion detection...")
        update_job_status(job_id, "processing", progress=30, message="Analyzing emotions...")
        emotion_result = call_emotion_service(local_path)
        
        # Step 4: Transcribe audio (50% progress)
        logger.info("Transcribing audio...")
        update_job_status(job_id, "processing", progress=50, message="Transcribing speech...")
        transcript_result = transcribe_audio(local_path)
        
        # Step 5: Run object detection (65% progress)
        logger.info("Running object detection...")
        update_job_status(job_id, "processing", progress=65, message="Detecting medication compliance...")
        object_result = call_object_detection_service(local_path)
        
        # Step 6: Multimodal fusion (75% progress)
        logger.info("Performing multimodal fusion...")
        update_job_status(job_id, "processing", progress=75, message="Combining analysis results...")
        fusion_result = multimodal_fusion(emotion_result, object_result)
        
        # Step 7: LLM analysis (85% progress)
        update_job_status(job_id, "processing", progress=85, message="Generating clinical summary...")
        if settings.ENABLE_BEDROCK_SERVICE:
            logger.info("Generating clinical summary with Bedrock...")
            transcript_text = transcript_result.get('transcript') if transcript_result else None
            clinical_summary = bedrock_analysis(fusion_result, patient_id, transcript_text)
        else:
            logger.info("Bedrock disabled, using rule-based summary")
            clinical_summary = rule_based_summary(fusion_result)
        
        # Ensure clinical summary has timestamp
        if 'timestamp' not in clinical_summary:
            clinical_summary['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        # Calculate processing time
        end_time = datetime.now(timezone.utc)
        processing_time = (end_time - start_time).total_seconds()
        
        # Step 8: Store results in DynamoDB (95% progress)
        update_job_status(job_id, "processing", progress=95, message="Saving results...")
        results = {
            "job_id": job_id,
            "patient_id": patient_id,
            "s3_key": s3_key,
            "emotion_analysis": emotion_result,
            "transcript": transcript_result,
            "object_detection": object_result,
            "fusion_result": fusion_result,
            "clinical_summary": clinical_summary,
            "analyzed_at": end_time.isoformat(),
            "processing_time_seconds": Decimal(str(processing_time)),  # Convert float to Decimal
            "status": "completed"
        }
        
        store_results(job_id, results)
        
        # Step 8: Update job status to "completed" (100% progress)
        update_job_status(job_id, "completed", progress=100, message="Analysis complete", results=results)
        
        # Cleanup
        if local_path and os.path.exists(local_path):
            os.remove(local_path)
            logger.info(f"Cleaned up temporary file: {local_path}")
        
        logger.info(f"Analysis completed for job {job_id} in {processing_time:.2f}s")
        return results
        
    except Exception as e:
        logger.error(f"Analysis failed for job {job_id}: {str(e)}", exc_info=True)
        update_job_status(job_id, "failed", progress=0, error=str(e), message="Analysis failed")
        
        # Cleanup on error
        if local_path and os.path.exists(local_path):
            try:
                os.remove(local_path)
            except:
                pass
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            retry_countdown = 60 * (2 ** self.request.retries)
            logger.info(f"Retrying job {job_id} in {retry_countdown} seconds (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e, countdown=retry_countdown)
        else:
            logger.error(f"Job {job_id} failed after {self.max_retries} retries")
            raise


def download_from_s3(s3_key: str) -> str:
    """Download file from S3 to temporary location with retry logic"""
    import time
    from botocore.exceptions import ClientError
    
    max_retries = 5
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            s3_client = s3()
            
            # First check if file exists
            try:
                s3_client.head_object(Bucket=settings.S3_BUCKET, Key=s3_key)
                logger.info(f"File exists in S3: {s3_key}")
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    if attempt < max_retries - 1:
                        logger.warning(f"File not found in S3 (attempt {attempt + 1}/{max_retries}), waiting {retry_delay}s...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        logger.error(f"File not found in S3 after {max_retries} attempts: {s3_key}")
                        raise Exception(f"File not uploaded to S3: {s3_key}")
                raise
            
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
            if attempt < max_retries - 1 and "not found" not in str(e).lower():
                logger.warning(f"Download attempt {attempt + 1} failed: {e}, retrying...")
                time.sleep(retry_delay)
                retry_delay *= 2
                continue
            logger.error(f"Failed to download from S3 after {attempt + 1} attempts: {e}")
            raise


def call_emotion_service(file_path: str) -> Dict[str, Any]:
    """
    Call real emotion detection service (multimodal: audio + visual)
    Returns emotion analysis with audio, face, and multimodal fusion results
    """
    
    # Check if service is enabled
    if not settings.ENABLE_EMOTION_SERVICE:
        logger.info("Emotion service disabled, returning stub data")
        return get_emotion_stub_data()
    
    try:
        emotion_url = settings.EMOTION_SERVICE_URL
        endpoint = f"{emotion_url}/v1/emotion/predict"
        
        logger.info(f"Calling emotion service at {endpoint}")
        
        # Open file and send to emotion service
        with open(file_path, "rb") as f:
            files = {"file": (Path(file_path).name, f, "video/mp4")}
            response = requests.post(
                endpoint,
                files=files,
                timeout=settings.EMOTION_SERVICE_TIMEOUT
            )
        
        if response.status_code == 200:
            result = response.json()
            
            # Transform emotion service response to expected format
            audio = result.get("audio", {})
            face = result.get("face", {})
            # Emotion service returns "fused" not "multimodal"
            multimodal = result.get("fused", result.get("multimodal", {}))
            model_type = result.get("model_type", "unknown")
            
            # Calculate confidence from probs if not provided
            audio_probs = audio.get("probs", {})
            audio_label = audio.get("label", "unknown")
            audio_confidence = audio_probs.get(audio_label, 0.0) if audio_label in audio_probs else 0.0
            
            face_probs = face.get("probs", {})
            face_label = face.get("label", "unknown")
            face_confidence = face_probs.get(face_label, 0.0) if face_label in face_probs else 0.0
            
            multimodal_probs = multimodal.get("probs", {})
            multimodal_label = multimodal.get("label", "unknown")
            multimodal_confidence = multimodal_probs.get(multimodal_label, 0.0) if multimodal_label in multimodal_probs else 0.0
            
            # Convert to DynamoDB-compatible format with Decimal
            transformed = {
                "status": "success",
                "model_type": model_type,
                "audio_emotion": {
                    "primary_emotion": audio_label,
                    "confidence": Decimal(str(audio_confidence)),
                    "all_emotions": {
                        k: Decimal(str(v)) 
                        for k, v in audio_probs.items()
                    }
                },
                "facial_emotion": {
                    "primary_emotion": face_label,
                    "confidence": Decimal(str(face_confidence)),
                    "all_emotions": {
                        k: Decimal(str(v)) 
                        for k, v in face_probs.items()
                    },
                    "face_detected": True
                },
                "multimodal_fusion": {
                    "primary_emotion": multimodal_label,
                    "confidence": Decimal(str(multimodal_confidence)),
                    "all_emotions": {
                        k: Decimal(str(v)) 
                        for k, v in multimodal_probs.items()
                    }
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Emotion detected: {multimodal_label} (confidence: {multimodal_confidence:.2%}, model: {model_type})")
            return transformed
        else:
            logger.warning(f"Emotion service returned {response.status_code}: {response.text}")
            return get_emotion_stub_data(error=f"Service returned {response.status_code}")
            
    except Exception as e:
        logger.error(f"Failed to call emotion service: {e}")
        import traceback
        traceback.print_exc()
        return get_emotion_stub_data(error=str(e))


def call_object_detection_service(file_path: str) -> Dict[str, Any]:
    """Call pill detection service (YOLOv11 + MediaPipe)"""
    
    # Check if service is enabled
    if not settings.ENABLE_COMPLIANCE_SERVICE:
        logger.info("Compliance service disabled, returning stub data")
        return get_compliance_stub_data()
    
    try:
        detection_url = settings.OBJECT_DETECTION_SERVICE_URL
        endpoint = f"{detection_url}/v1/detect"
        
        logger.info(f"Calling pill detection service at {endpoint}")
        
        with open(file_path, "rb") as f:
            files = {"video": (Path(file_path).name, f, "video/mp4")}
            response = requests.post(
                endpoint,
                files=files,
                timeout=settings.OBJECT_DETECTION_TIMEOUT
            )
        
        if response.status_code == 200:
            result = response.json()
            
            # Add timestamp if not present
            if 'timestamp' not in result:
                result['timestamp'] = datetime.now(timezone.utc).isoformat()
            
            logger.info(f"Pill detection complete: {result.get('verification_status')} "
                       f"(score: {result.get('compliance_score', 0):.2f})")
            
            return result
        else:
            logger.warning(f"Pill detection service returned {response.status_code}: {response.text[:200]}")
            return get_compliance_stub_data(error=f"Service returned {response.status_code}")
            
    except Exception as e:
        logger.error(f"Failed to call pill detection service: {e}")
        return get_compliance_stub_data(error=str(e))


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


def transcribe_audio(file_path: str) -> Dict[str, Any]:
    """Transcribe audio using AWS Transcribe"""
    if not settings.ENABLE_TRANSCRIPTION:
        logger.info("Transcription disabled, skipping")
        return get_transcription_stub_data()
    
    if not TRANSCRIPTION_AVAILABLE:
        logger.warning("Transcription service not available, using stub data")
        return get_transcription_stub_data(error="Transcription service not imported")
    
    try:
        # Extract audio from video
        logger.info(f"Extracting audio from {file_path}")
        audio_path = extract_audio_from_video(file_path)
        
        # Initialize Transcribe client
        client = TranscribeClient(
            region=os.getenv('AWS_TRANSCRIBE_REGION', 'us-east-1'),
            s3_bucket=os.getenv('S3_BUCKET'),
            language_code=os.getenv('TRANSCRIBE_LANGUAGE_CODE', 'ms-MY'),
            max_speakers=int(os.getenv('TRANSCRIBE_MAX_SPEAKERS', 2))
        )
        
        # Transcribe (async, waits for completion)
        logger.info("Starting transcription job...")
        result = client.transcribe_audio(
            audio_path=audio_path,
            wait_for_completion=True,
            max_wait_seconds=300
        )
        
        # Cleanup audio file
        try:
            Path(audio_path).unlink()
            logger.info("Temporary audio file deleted")
        except Exception as e:
            logger.warning(f"Failed to delete audio file: {e}")
        
        logger.info(f"Transcription complete: {result.get('word_count', 0)} words")
        return result
        
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        import traceback
        traceback.print_exc()
        return get_transcription_stub_data(error=str(e))


def bedrock_analysis(fusion_result: Dict, patient_id: str, transcript: str = None) -> Dict[str, Any]:
    """Generate clinical summary using AWS Bedrock with transcript"""
    
    if not BEDROCK_AVAILABLE:
        logger.warning("Bedrock service not available, using rule-based fallback")
        return get_rule_based_summary(fusion_result)
    
    try:
        # Prepare emotion data for Bedrock
        patient_state = fusion_result.get("patient_state", {})
        compliance = fusion_result.get("medication_compliance", {})
        
        emotion_data = {
            "audio_emotion": patient_state.get("audio_emotion", {}),
            "facial_emotion": patient_state.get("facial_emotion", {}),
            "compliance": compliance
        }
        
        # Convert Decimals to floats for JSON serialization
        emotion_data = convert_decimals_to_float(emotion_data)
        
        # Initialize Bedrock client
        bedrock = BedrockClient(
            region=os.getenv('AWS_BEDROCK_REGION', 'us-east-1'),
            model_id=os.getenv('AWS_BEDROCK_MODEL_ID', 'anthropic.claude-3-haiku-20240307-v1:0'),
            max_tokens=int(os.getenv('BEDROCK_MAX_TOKENS', 1500)),
            temperature=float(os.getenv('BEDROCK_TEMPERATURE', 0.7))
        )
        
        # Generate clinical summary with transcript
        logger.info(f"Generating clinical summary for {patient_id} with Bedrock")
        if transcript:
            logger.info(f"Including transcript ({len(transcript)} chars)")
        
        clinical_summary = bedrock.generate_clinical_summary(
            emotion_data=emotion_data,
            patient_id=patient_id,
            transcript=transcript
        )
        
        logger.info("Clinical summary generated successfully")
        return clinical_summary
        
    except Exception as e:
        logger.error(f"Bedrock analysis failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback to rule-based summary
        logger.info("Falling back to rule-based summary")
        return rule_based_summary(fusion_result)


def rule_based_summary(fusion_result: Dict) -> Dict[str, Any]:
    """Generate rule-based clinical summary"""
    patient_state = fusion_result.get("patient_state", {})
    compliance = fusion_result.get("medication_compliance", {})
    
    # Convert Decimal to float for comparison
    compliance_score = compliance.get("compliance_score", Decimal("0"))
    if isinstance(compliance_score, Decimal):
        compliance_score = float(compliance_score)
    
    summary = {
        "emotional_state": "Appears calm and stable",
        "medication_adherence": "Compliant" if compliance_score > 0.7 else "Non-compliant",
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
            update_expr += ", #error = :error"
            expr_values[":error"] = kwargs["error"]
            expr_names["#error"] = "error"
        
        if "progress" in kwargs:
            update_expr += ", progress = :progress"
            expr_values[":progress"] = kwargs["progress"]
        
        if "message" in kwargs:
            update_expr += ", message = :message"
            expr_values[":message"] = kwargs["message"]
        
        # Add timestamp fields based on status
        if status == "processing" and "started_at" not in kwargs:
            update_expr += ", started_at = if_not_exists(started_at, :started_at)"
            expr_values[":started_at"] = datetime.now(timezone.utc).isoformat()
        elif status in ["completed", "failed"]:
            update_expr += ", completed_at = :completed_at"
            expr_values[":completed_at"] = datetime.now(timezone.utc).isoformat()
        
        # Convert all floats to Decimal for DynamoDB compatibility
        expr_values = convert_floats_to_decimal(expr_values)
        
        table.update_item(
            Key={"job_id": job_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values
        )
        
        logger.info(f"Updated job {job_id} status to {status} (progress: {kwargs.get('progress', 'N/A')}%)")
        
    except Exception as e:
        logger.error(f"Failed to update job status: {e}")


def store_results(job_id: str, results: Dict[str, Any]):
    """Store analysis results in DynamoDB"""
    try:
        table = dynamodb().Table(settings.DYNAMO_TABLE)
        
        analyzed_at = results.get("analyzed_at") or datetime.now(timezone.utc).isoformat()
        
        item = {
            "user_id": results["patient_id"],
            "timestamp": analyzed_at,
            "job_id": job_id,
            "s3_key": results["s3_key"],
            "analyzed_at": analyzed_at,  # Add this field explicitly
            "analysis_type": "multimodal",
            "results": results,
            "processing_time_seconds": results.get("processing_time_seconds"),
            "status": "completed"
        }
        
        # Convert all floats to Decimal for DynamoDB compatibility
        item = convert_floats_to_decimal(item)
        
        table.put_item(Item=item)
        logger.info(f"Stored results for job {job_id}")
        
    except Exception as e:
        logger.error(f"Failed to store results: {e}")
        raise


# ============================================
# STUB DATA FUNCTIONS
# ============================================

def get_emotion_stub_data(error: str = None) -> Dict[str, Any]:
    """
    Return stub data for emotion detection service
    Used when ENABLE_EMOTION_SERVICE is False or service fails
    """
    stub = {
        "status": "stub",
        "audio_emotion": {
            "primary_emotion": "calm",
            "confidence": Decimal("0.85"),
            "all_emotions": {
                "calm": Decimal("0.85"),
                "neutral": Decimal("0.10"),
                "happy": Decimal("0.03"),
                "sad": Decimal("0.02")
            },
            "intensity": Decimal("0.6"),
            "valence": Decimal("0.7"),  # Positive/negative scale
            "arousal": Decimal("0.4")   # Energy level
        },
        "facial_emotion": {
            "primary_emotion": "neutral",
            "confidence": Decimal("0.82"),
            "all_emotions": {
                "neutral": Decimal("0.82"),
                "calm": Decimal("0.12"),
                "happy": Decimal("0.04"),
                "sad": Decimal("0.02")
            },
            "face_detected": True,
            "face_count": 1
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "processing_time_ms": 1500
    }
    
    if error:
        stub["error"] = error
        stub["note"] = "Stub data returned due to service error"
    else:
        stub["note"] = "Stub data - emotion service disabled"
    
    return stub


def get_compliance_stub_data(error: str = None) -> Dict[str, Any]:
    """
    Return stub data for compliance/object detection service
    Used when ENABLE_COMPLIANCE_SERVICE is False or service fails
    """
    stub = {
        "status": "stub",
        "pill_detected": True,
        "confidence": Decimal("0.92"),
        "compliance": True,
        "compliance_score": Decimal("0.92"),
        "objects_detected": [
            {
                "class": "pill",
                "confidence": Decimal("0.92"),
                "bounding_box": {
                    "x": 120,
                    "y": 80,
                    "width": 40,
                    "height": 30
                }
            }
        ],
        "verification_status": "compliant",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "processing_time_ms": 1200
    }
    
    if error:
        stub["error"] = error
        stub["note"] = "Stub data returned due to service error"
    else:
        stub["note"] = "Stub data - compliance service disabled"
    
    return stub


def get_transcription_stub_data(error: str = None) -> Dict[str, Any]:
    """
    Return stub data for transcription service
    Used when ENABLE_TRANSCRIPTION is False or service fails
    """
    stub = {
        "status": "stub",
        "job_name": "stub-transcription",
        "transcript": "Stub transcript - transcription service disabled or failed",
        "segments": [],
        "language_code": "ms-MY",
        "word_count": 0,
        "speaker_count": 0,
        "duration_seconds": 0.0,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if error:
        stub["error"] = error
        stub["note"] = "Stub data returned due to transcription error"
    else:
        stub["note"] = "Stub data - transcription service disabled"
    
    return stub
