# app/repositories/results_repository.py
"""
Repository for analysis results in DynamoDB
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

from core.aws import dynamodb
from core.config import settings


class ResultsRepository:
    """Handles analysis result storage and retrieval"""
    
    def __init__(self):
        self.table_name = settings.DYNAMO_TABLE
        self._table = None
    
    @property
    def table(self):
        """Lazy load DynamoDB table"""
        if self._table is None:
            self._table = dynamodb().Table(self.table_name)
        return self._table
    
    def save_result(
        self,
        job_id: str,
        patient_id: str,
        s3_key: str,
        results: Dict[str, Any],
        processing_time_seconds: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Save analysis results
        
        Args:
            job_id: Job identifier
            patient_id: Patient identifier (partition key)
            s3_key: S3 object key
            results: Complete analysis results
            processing_time_seconds: Time taken for analysis
            
        Returns:
            Saved item
        """
        now = datetime.now(timezone.utc).isoformat()
        
        item = {
            "user_id": patient_id,  # Partition key
            "timestamp": now,  # Sort key
            "job_id": job_id,
            "s3_key": s3_key,
            "analysis_type": "multimodal",
            "results": results,
            "analyzed_at": now,
            "processing_time_seconds": processing_time_seconds,
            "status": "completed"
        }
        
        try:
            self.table.put_item(Item=item)
            return item
        except ClientError as e:
            raise Exception(f"Failed to save result: {e.response['Error']['Message']}")
    
    def get_latest_results(
        self,
        patient_id: str,
        limit: int = 10,
        last_evaluated_key: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get latest results for a patient
        
        Args:
            patient_id: Patient identifier
            limit: Maximum number of results
            last_evaluated_key: Pagination token
            
        Returns:
            Dict with items and optional next token
        """
        try:
            query_kwargs = {
                "KeyConditionExpression": Key('user_id').eq(patient_id),
                "Limit": limit,
                "ScanIndexForward": False  # Most recent first (descending timestamp)
            }
            
            if last_evaluated_key:
                query_kwargs["ExclusiveStartKey"] = last_evaluated_key
            
            response = self.table.query(**query_kwargs)
            
            return {
                "items": response.get("Items", []),
                "next_token": response.get("LastEvaluatedKey"),
                "count": response.get("Count", 0)
            }
        except ClientError as e:
            raise Exception(f"Failed to get results: {e.response['Error']['Message']}")
    
    def get_result_by_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get result by job ID (requires scan or GSI)
        
        Args:
            job_id: Job identifier
            
        Returns:
            Result item or None
        """
        try:
            # DynamoDB scans with FilterExpression can have consistency issues
            # So we scan recent items and filter in Python for reliability
            response = self.table.scan(
                Limit=100  # Scan recent items
            )
            
            # Filter in Python for better consistency
            items = response.get("Items", [])
            for item in items:
                if item.get("job_id") == job_id:
                    return item
            
            # If not found in first batch, continue scanning
            while 'LastEvaluatedKey' in response and len(items) < 500:
                response = self.table.scan(
                    Limit=100,
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                items = response.get("Items", [])
                for item in items:
                    if item.get("job_id") == job_id:
                        return item
            
            return None
        except ClientError as e:
            raise Exception(f"Failed to get result by job: {e.response['Error']['Message']}")
    
    def count_results_for_patient(self, patient_id: str) -> int:
        """
        Count total results for a patient
        
        Args:
            patient_id: Patient identifier
            
        Returns:
            Count of results
        """
        try:
            response = self.table.query(
                KeyConditionExpression=Key('user_id').eq(patient_id),
                Select="COUNT"
            )
            return response.get("Count", 0)
        except ClientError as e:
            raise Exception(f"Failed to count results: {e.response['Error']['Message']}")


# Singleton instance
results_repo = ResultsRepository()
