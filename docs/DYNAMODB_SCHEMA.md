# DynamoDB Schema Documentation

## Overview

SchizoDot AI uses two DynamoDB tables for data persistence:

1. **SchizodotJobs** - Job tracking and status
2. **SchizodotUsers** - Analysis results and patient history

---

## Table 1: SchizodotJobs

### Purpose
Tracks analysis job lifecycle from creation to completion.

### Schema

**Partition Key**: `job_id` (String)

**Attributes**:
- `job_id` (String, PK) - Unique job identifier (e.g., "job-abc123def456")
- `patient_id` (String) - Patient identifier
- `status` (String) - Job status: `queued`, `processing`, `completed`, `failed`
- `s3_key` (String) - S3 object key for uploaded media
- `filename` (String) - Original filename
- `content_type` (String) - MIME type (e.g., "video/mp4")
- `created_at` (String) - ISO 8601 timestamp
- `updated_at` (String) - ISO 8601 timestamp
- `started_at` (String, optional) - When processing began
- `completed_at` (String, optional) - When job finished
- `progress` (Number, optional) - Progress percentage (0-100)
- `message` (String, optional) - Status message
- `error` (String, optional) - Error message if failed
- `results` (Map, optional) - Summary of analysis results
- `metadata` (Map, optional) - Additional metadata

### Global Secondary Index (GSI)

**Index Name**: `patient_id-created_at-index`
- **Partition Key**: `patient_id`
- **Sort Key**: `created_at`
- **Purpose**: Query all jobs for a patient, sorted by creation time

### AWS CLI Creation Command

```bash
aws dynamodb create-table \
    --table-name SchizodotJobs \
    --attribute-definitions \
        AttributeName=job_id,AttributeType=S \
        AttributeName=patient_id,AttributeType=S \
        AttributeName=created_at,AttributeType=S \
    --key-schema \
        AttributeName=job_id,KeyType=HASH \
    --global-secondary-indexes \
        "[
            {
                \"IndexName\": \"patient_id-created_at-index\",
                \"KeySchema\": [
                    {\"AttributeName\":\"patient_id\",\"KeyType\":\"HASH\"},
                    {\"AttributeName\":\"created_at\",\"KeyType\":\"RANGE\"}
                ],
                \"Projection\": {\"ProjectionType\":\"ALL\"},
                \"ProvisionedThroughput\": {
                    \"ReadCapacityUnits\": 5,
                    \"WriteCapacityUnits\": 5
                }
            }
        ]" \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region us-east-1
```

### Example Item

```json
{
  "job_id": "job-abc123def456",
  "patient_id": "patient-001",
  "status": "completed",
  "s3_key": "uploads/patient-001/20240115T120000Z_checkin.mp4",
  "filename": "checkin-2024-01-15.mp4",
  "content_type": "video/mp4",
  "created_at": "2024-01-15T12:00:00Z",
  "updated_at": "2024-01-15T12:05:30Z",
  "started_at": "2024-01-15T12:01:00Z",
  "completed_at": "2024-01-15T12:05:30Z",
  "progress": 100,
  "message": "Analysis completed successfully",
  "error": null,
  "results": {
    "emotion_summary": "calm",
    "compliance_score": 0.95,
    "risk_level": "low"
  },
  "metadata": {
    "session_type": "weekly_checkin"
  }
}
```

---

## Table 2: SchizodotUsers

### Purpose
Stores complete analysis results and patient history.

### Schema

**Partition Key**: `user_id` (String)  
**Sort Key**: `timestamp` (String)

**Attributes**:
- `user_id` (String, PK) - Patient identifier (same as `patient_id`)
- `timestamp` (String, SK) - ISO 8601 timestamp (sort key for chronological order)
- `job_id` (String) - Reference to job in SchizodotJobs table
- `s3_key` (String) - S3 object key
- `analysis_type` (String) - Type of analysis (e.g., "multimodal")
- `analyzed_at` (String) - ISO 8601 timestamp
- `processing_time_seconds` (Number, optional) - Time taken for analysis
- `status` (String) - "completed"
- `results` (Map) - Complete analysis results including:
  - `audio_emotion` (Map)
  - `facial_emotion` (Map)
  - `compliance` (Map)
  - `multimodal_fusion` (Map)
  - `clinical_summary` (Map)

### AWS CLI Creation Command

```bash
aws dynamodb create-table \
    --table-name SchizodotUsers \
    --attribute-definitions \
        AttributeName=user_id,AttributeType=S \
        AttributeName=timestamp,AttributeType=S \
    --key-schema \
        AttributeName=user_id,KeyType=HASH \
        AttributeName=timestamp,KeyType=RANGE \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region us-east-1
```

### Example Item

```json
{
  "user_id": "patient-001",
  "timestamp": "2024-01-15T12:05:30Z",
  "job_id": "job-abc123def456",
  "s3_key": "uploads/patient-001/20240115T120000Z_checkin.mp4",
  "analysis_type": "multimodal",
  "analyzed_at": "2024-01-15T12:05:30Z",
  "processing_time_seconds": 45.2,
  "status": "completed",
  "results": {
    "audio_emotion": {
      "primary_emotion": "calm",
      "confidence": 0.87,
      "all_emotions": [
        {"emotion": "calm", "confidence": 0.87},
        {"emotion": "neutral", "confidence": 0.10}
      ]
    },
    "facial_emotion": {
      "primary_emotion": "neutral",
      "confidence": 0.82,
      "all_emotions": [
        {"emotion": "neutral", "confidence": 0.82},
        {"emotion": "calm", "confidence": 0.15}
      ],
      "face_detected": true,
      "frame_count": 150
    },
    "compliance": {
      "pill_detected": true,
      "hand_detected": true,
      "face_detected": true,
      "compliance_score": 0.95,
      "confidence": 0.90,
      "verification_status": "compliant"
    },
    "multimodal_fusion": {
      "emotional_consistency": "consistent",
      "overall_emotion": "calm",
      "confidence": 0.85,
      "risk_level": "low",
      "risk_factors": []
    },
    "clinical_summary": {
      "emotional_state": "Patient appears calm and stable",
      "medication_adherence": "Compliant - medication taken as prescribed",
      "risk_assessment": "Low risk - no concerning indicators",
      "recommendations": [
        "Continue current treatment plan",
        "Schedule routine follow-up"
      ],
      "generated_by": "rule_based",
      "timestamp": "2024-01-15T12:05:30Z"
    }
  }
}
```

---

## Access Patterns

### 1. Create Job
- **Table**: SchizodotJobs
- **Operation**: PutItem
- **Key**: `job_id`

### 2. Get Job Status
- **Table**: SchizodotJobs
- **Operation**: GetItem
- **Key**: `job_id`

### 3. Update Job Status
- **Table**: SchizodotJobs
- **Operation**: UpdateItem
- **Key**: `job_id`

### 4. List Jobs for Patient
- **Table**: SchizodotJobs
- **Operation**: Query (GSI)
- **Index**: `patient_id-created_at-index`
- **Key**: `patient_id`
- **Sort**: `created_at` (descending)

### 5. Save Analysis Result
- **Table**: SchizodotUsers
- **Operation**: PutItem
- **Key**: `user_id`, `timestamp`

### 6. Get Latest Results for Patient
- **Table**: SchizodotUsers
- **Operation**: Query
- **Key**: `user_id`
- **Sort**: `timestamp` (descending)
- **Limit**: 10 (configurable)

---

## Cost Estimation

### Provisioned Capacity (Development)
- **SchizodotJobs**: 5 RCU, 5 WCU
- **SchizodotUsers**: 5 RCU, 5 WCU
- **GSI**: 5 RCU, 5 WCU

**Estimated Monthly Cost**: ~$3-5 USD

### On-Demand (Production Recommended)
- Pay per request
- Auto-scales
- **Estimated Cost**: $1.25 per million write requests, $0.25 per million read requests

---

## Setup Instructions

### 1. Create Tables via AWS CLI

```bash
# Set your AWS region
export AWS_REGION=us-east-1

# Create SchizodotJobs table
aws dynamodb create-table --cli-input-json file://dynamodb-jobs-table.json

# Create SchizodotUsers table
aws dynamodb create-table --cli-input-json file://dynamodb-users-table.json
```

### 2. Verify Tables

```bash
# List tables
aws dynamodb list-tables --region us-east-1

# Describe SchizodotJobs
aws dynamodb describe-table --table-name SchizodotJobs --region us-east-1

# Describe SchizodotUsers
aws dynamodb describe-table --table-name SchizodotUsers --region us-east-1
```

### 3. Update .env

```bash
DYNAMO_TABLE=SchizodotUsers
DYNAMO_TABLE_JOBS=SchizodotJobs
AWS_REGION=us-east-1
```

---

## Migration & Backup

### Export Table

```bash
aws dynamodb scan --table-name SchizodotJobs \
    --region us-east-1 \
    --output json > jobs-backup.json
```

### Point-in-Time Recovery

Enable PITR for production:

```bash
aws dynamodb update-continuous-backups \
    --table-name SchizodotJobs \
    --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
```

---

## Monitoring

### CloudWatch Metrics
- `ConsumedReadCapacityUnits`
- `ConsumedWriteCapacityUnits`
- `UserErrors`
- `SystemErrors`

### Alarms (Recommended)
- High throttling rate
- High error rate
- Capacity utilization > 80%

---

## Next Steps

1. Create tables in AWS Console or via CLI
2. Test with sample data
3. Verify IAM permissions for Lambda/EC2
4. Enable monitoring and alarms
5. Consider switching to On-Demand for production
