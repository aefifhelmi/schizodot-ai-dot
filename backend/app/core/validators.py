# app/core/validators.py
"""
Validation utilities for request data
"""
import re
from typing import Optional
from core.exceptions import validation_error_exception


# Allowed MIME types
ALLOWED_VIDEO_TYPES = [
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "video/mpeg",
]

ALLOWED_AUDIO_TYPES = [
    "audio/mpeg",
    "audio/wav",
    "audio/x-wav",
    "audio/mp4",
]

ALLOWED_CONTENT_TYPES = ALLOWED_VIDEO_TYPES + ALLOWED_AUDIO_TYPES


def validate_patient_id(patient_id: str) -> str:
    """
    Validate patient ID format
    
    Rules:
    - 3-100 characters
    - Alphanumeric, hyphens, underscores only
    - Cannot start with hyphen or underscore
    
    Raises:
        HTTPException: If validation fails
    """
    if not patient_id:
        raise validation_error_exception("patient_id", "Patient ID is required")
    
    if len(patient_id) < 3:
        raise validation_error_exception("patient_id", "Patient ID must be at least 3 characters")
    
    if len(patient_id) > 100:
        raise validation_error_exception("patient_id", "Patient ID must be at most 100 characters")
    
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*$', patient_id):
        raise validation_error_exception(
            "patient_id",
            "Patient ID must start with alphanumeric and contain only letters, numbers, hyphens, and underscores"
        )
    
    return patient_id


def validate_filename(filename: str) -> str:
    """
    Validate filename
    
    Rules:
    - 1-255 characters
    - Must have an extension
    - No path traversal characters
    
    Raises:
        HTTPException: If validation fails
    """
    if not filename:
        raise validation_error_exception("filename", "Filename is required")
    
    if len(filename) > 255:
        raise validation_error_exception("filename", "Filename must be at most 255 characters")
    
    # Check for path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise validation_error_exception("filename", "Filename cannot contain path separators")
    
    # Must have extension
    if "." not in filename:
        raise validation_error_exception("filename", "Filename must have an extension")
    
    return filename


def validate_content_type(content_type: str) -> str:
    """
    Validate content type
    
    Raises:
        HTTPException: If content type not allowed
    """
    if not content_type:
        raise validation_error_exception("content_type", "Content type is required")
    
    if content_type not in ALLOWED_CONTENT_TYPES:
        from core.exceptions import invalid_content_type_exception
        raise invalid_content_type_exception(content_type, ALLOWED_CONTENT_TYPES)
    
    return content_type


def validate_job_id(job_id: str) -> str:
    """
    Validate job ID format
    
    Rules:
    - Must start with "job-"
    - 16-50 characters total
    
    Raises:
        HTTPException: If validation fails
    """
    if not job_id:
        raise validation_error_exception("job_id", "Job ID is required")
    
    if not job_id.startswith("job-"):
        raise validation_error_exception("job_id", "Job ID must start with 'job-'")
    
    if len(job_id) < 16 or len(job_id) > 50:
        raise validation_error_exception("job_id", "Invalid job ID format")
    
    return job_id


def validate_pagination_limit(limit: int, max_limit: int = 100) -> int:
    """
    Validate pagination limit
    
    Args:
        limit: Requested limit
        max_limit: Maximum allowed limit
    
    Returns:
        Validated limit
    
    Raises:
        HTTPException: If limit is invalid
    """
    if limit < 1:
        raise validation_error_exception("limit", "Limit must be at least 1")
    
    if limit > max_limit:
        raise validation_error_exception("limit", f"Limit cannot exceed {max_limit}")
    
    return limit


def sanitize_metadata(metadata: Optional[dict]) -> dict:
    """
    Sanitize metadata dictionary
    
    - Remove None values
    - Limit size
    - Convert to JSON-serializable types
    
    Args:
        metadata: Raw metadata dict
    
    Returns:
        Sanitized metadata
    """
    if not metadata:
        return {}
    
    # Remove None values
    sanitized = {k: v for k, v in metadata.items() if v is not None}
    
    # Limit number of keys
    if len(sanitized) > 50:
        raise validation_error_exception("metadata", "Metadata cannot have more than 50 keys")
    
    # Limit size of each value
    for key, value in sanitized.items():
        if isinstance(value, str) and len(value) > 1000:
            raise validation_error_exception(
                f"metadata.{key}",
                "Metadata values cannot exceed 1000 characters"
            )
    
    return sanitized
