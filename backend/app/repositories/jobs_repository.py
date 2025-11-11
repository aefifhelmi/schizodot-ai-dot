# app/repositories/jobs_repository.py
"""
Repository for job management in DynamoDB
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError

from core.aws import dynamodb
from core.config import settings
from schemas.jobs import JobStatus


class JobsRepository:
    """Handles job CRUD operations in DynamoDB"""
    
    def __init__(self):
        self.table_name = settings.DYNAMO_TABLE_JOBS
        self._table = None
    
    @property
    def table(self):
        """Lazy load DynamoDB table"""
        if self._table is None:
            self._table = dynamodb().Table(self.table_name)
        return self._table
    
    def create_job(
        self,
        patient_id: str,
        s3_key: str,
        filename: str,
        content_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new job record
        
        Args:
            patient_id: Patient identifier
            s3_key: S3 object key
            filename: Original filename
            content_type: MIME type
            metadata: Additional metadata
            
        Returns:
            Created job record
        """
        job_id = f"job-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        
        item = {
            "job_id": job_id,
            "patient_id": patient_id,
            "status": JobStatus.QUEUED.value,
            "s3_key": s3_key,
            "filename": filename,
            "content_type": content_type,
            "created_at": now,
            "updated_at": now,
            "metadata": metadata or {}
        }
        
        try:
            self.table.put_item(Item=item)
            return item
        except ClientError as e:
            raise Exception(f"Failed to create job: {e.response['Error']['Message']}")
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a job by ID
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job record or None if not found
        """
        try:
            response = self.table.get_item(Key={"job_id": job_id})
            return response.get("Item")
        except ClientError as e:
            raise Exception(f"Failed to get job: {e.response['Error']['Message']}")
    
    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        error: Optional[str] = None,
        results: Optional[Dict[str, Any]] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update job status and related fields
        
        Args:
            job_id: Job identifier
            status: New status
            error: Error message if failed
            results: Analysis results if completed
            progress: Progress percentage (0-100)
            message: Status message
            
        Returns:
            Updated job record
        """
        now = datetime.now(timezone.utc).isoformat()
        
        # Build update expression dynamically
        update_expr = "SET #status = :status, updated_at = :updated_at"
        expr_attr_names = {"#status": "status"}
        expr_attr_values = {
            ":status": status.value,
            ":updated_at": now
        }
        
        # Add timestamp fields based on status
        if status == JobStatus.PROCESSING:
            update_expr += ", started_at = :started_at"
            expr_attr_values[":started_at"] = now
        elif status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            update_expr += ", completed_at = :completed_at"
            expr_attr_values[":completed_at"] = now
        
        # Add optional fields
        if error is not None:
            update_expr += ", error = :error"
            expr_attr_values[":error"] = error
        
        if results is not None:
            update_expr += ", results = :results"
            expr_attr_values[":results"] = results
        
        if progress is not None:
            update_expr += ", progress = :progress"
            expr_attr_values[":progress"] = progress
        
        if message is not None:
            update_expr += ", message = :message"
            expr_attr_values[":message"] = message
        
        try:
            response = self.table.update_item(
                Key={"job_id": job_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values,
                ReturnValues="ALL_NEW"
            )
            return response.get("Attributes", {})
        except ClientError as e:
            raise Exception(f"Failed to update job: {e.response['Error']['Message']}")
    
    def list_jobs_by_patient(
        self,
        patient_id: str,
        limit: int = 20,
        last_evaluated_key: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        List jobs for a patient
        
        Args:
            patient_id: Patient identifier
            limit: Maximum number of results
            last_evaluated_key: Pagination token
            
        Returns:
            Dict with items and optional next token
        """
        try:
            query_kwargs = {
                "IndexName": "patient_id-created_at-index",  # GSI needed
                "KeyConditionExpression": "patient_id = :patient_id",
                "ExpressionAttributeValues": {":patient_id": patient_id},
                "Limit": limit,
                "ScanIndexForward": False  # Most recent first
            }
            
            if last_evaluated_key:
                query_kwargs["ExclusiveStartKey"] = last_evaluated_key
            
            response = self.table.query(**query_kwargs)
            
            return {
                "items": response.get("Items", []),
                "next_token": response.get("LastEvaluatedKey")
            }
        except ClientError as e:
            raise Exception(f"Failed to list jobs: {e.response['Error']['Message']}")


# Singleton instance
jobs_repo = JobsRepository()
