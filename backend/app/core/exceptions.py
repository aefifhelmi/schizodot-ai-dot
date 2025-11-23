# app/core/exceptions.py
"""
Custom exception classes for the application
"""
from fastapi import HTTPException, status
from typing import Optional, Dict, Any


class SchizoDotException(Exception):
    """Base exception for SchizoDot AI"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class JobNotFoundException(SchizoDotException):
    """Raised when a job is not found"""
    pass


class ResultNotFoundException(SchizoDotException):
    """Raised when a result is not found"""
    pass


class InvalidContentTypeException(SchizoDotException):
    """Raised when content type is not allowed"""
    pass


class DynamoDBException(SchizoDotException):
    """Raised when DynamoDB operation fails"""
    pass


class S3Exception(SchizoDotException):
    """Raised when S3 operation fails"""
    pass


class CeleryTaskException(SchizoDotException):
    """Raised when Celery task fails"""
    pass


def job_not_found_exception(job_id: str) -> HTTPException:
    """Create a 404 exception for job not found"""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "error": "Job not found",
            "message": f"Job '{job_id}' does not exist",
            "hint": "Check the job_id or create a new analysis job"
        }
    )


def result_not_found_exception(identifier: str, identifier_type: str = "patient") -> HTTPException:
    """Create a 404 exception for result not found"""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "error": "Result not found",
            "message": f"No results found for {identifier_type} '{identifier}'",
            "hint": "The job may still be processing or may have failed"
        }
    )


def invalid_content_type_exception(content_type: str, allowed_types: list) -> HTTPException:
    """Create a 400 exception for invalid content type"""
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "error": "Invalid content type",
            "message": f"Content type '{content_type}' is not allowed",
            "allowed_types": allowed_types,
            "hint": "Use video/mp4, audio/wav, or other supported formats"
        }
    )


def validation_error_exception(field: str, message: str) -> HTTPException:
    """Create a 422 exception for validation errors"""
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "error": "Validation error",
            "field": field,
            "message": message
        }
    )


def internal_server_error_exception(operation: str, error: str) -> HTTPException:
    """Create a 500 exception for internal errors"""
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "error": "Internal server error",
            "operation": operation,
            "message": f"Failed to {operation}",
            "details": error
        }
    )
