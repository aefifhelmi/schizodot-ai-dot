# SchizoDot AI - API Documentation

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://api.schizodot.ai` (TBD)

All API endpoints are prefixed with `/api/v1`.

---

## Authentication

Currently, the API does not require authentication. In production, implement:
- API Keys for service-to-service
- JWT tokens for user authentication
- OAuth2 for third-party integrations

---

## Common Response Formats

### Success Response
```json
{
  "data": {...},
  "status": "success"
}
```

### Error Response
```json
{
  "error": "Error type",
  "message": "Human-readable error message",
  "details": "Additional error details",
  "hint": "Suggestion for fixing the error"
}
```

---

## Endpoints

### 1. Health Check

#### `GET /api/v1/health/`

Check API health status.

**Response**: `200 OK`
```json
{
  "status": "ok"
}
```

---

### 2. Create Analysis Job

#### `POST /api/v1/analyze/`

Create a new analysis job and get a presigned S3 upload URL.

**Request Body**:
```json
{
  "patient_id": "patient-001",
  "filename": "checkin-2024-01-15.mp4",
  "content_type": "video/mp4",
  "metadata": {
    "session_type": "weekly_checkin",
    "notes": "Patient seems stable"
  }
}
```

**Validation Rules**:
- `patient_id`: 3-100 characters, alphanumeric + hyphens/underscores
- `filename`: 1-255 characters, must have extension, no path separators
- `content_type`: Must be one of:
  - Video: `video/mp4`, `video/quicktime`, `video/x-msvideo`, `video/mpeg`
  - Audio: `audio/mpeg`, `audio/wav`, `audio/x-wav`, `audio/mp4`
- `metadata`: Optional, max 50 keys, values max 1000 characters

**Response**: `201 Created`
```json
{
  "job_id": "job-abc123def456",
  "patient_id": "patient-001",
  "status": "queued",
  "s3_key": "uploads/patient-001/20240115T120000Z_checkin.mp4",
  "presigned_url": "https://s3.amazonaws.com/bucket/...",
  "presigned_url_expires_in": 900,
  "created_at": "2024-01-15T12:00:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid content type or validation error
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Database or S3 error

**Usage Flow**:
1. Call this endpoint to get `presigned_url` and `job_id`
2. Upload file directly to S3 using the presigned URL (PUT request)
3. Poll `/jobs/{job_id}/status` to track progress

---

### 3. Get Job Status

#### `GET /api/v1/jobs/{job_id}/status`

Get the current status of an analysis job.

**Path Parameters**:
- `job_id`: Job identifier (format: `job-XXXXXXXXXXXX`)

**Response**: `200 OK`
```json
{
  "job_id": "job-abc123def456",
  "status": "processing",
  "progress": 65,
  "message": "Running emotion detection...",
  "error": null,
  "created_at": "2024-01-15T12:00:00Z",
  "updated_at": "2024-01-15T12:03:00Z",
  "results_available": false
}
```

**Status Values**:
- `queued`: Job created, waiting to start
- `processing`: Analysis in progress
- `completed`: Analysis finished successfully
- `failed`: Analysis failed (check `error` field)

**Error Responses**:
- `404 Not Found`: Job doesn't exist
- `422 Unprocessable Entity`: Invalid job ID format
- `500 Internal Server Error`: Database error

---

### 4. Get Complete Job Details

#### `GET /api/v1/jobs/{job_id}`

Get complete job information including results if available.

**Path Parameters**:
- `job_id`: Job identifier

**Response**: `200 OK`
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
  "error": null,
  "results": {
    "emotion_summary": "calm",
    "compliance_score": 0.95,
    "risk_level": "low"
  }
}
```

---

### 5. List Jobs for Patient

#### `GET /api/v1/jobs/patient/{patient_id}`

List all jobs for a specific patient.

**Path Parameters**:
- `patient_id`: Patient identifier

**Query Parameters**:
- `limit` (optional): Max results (1-100, default 20)
- `status_filter` (optional): Filter by status (`queued`, `processing`, `completed`, `failed`)

**Response**: `200 OK`
```json
[
  {
    "job_id": "job-abc123",
    "patient_id": "patient-001",
    "status": "completed",
    ...
  },
  {
    "job_id": "job-def456",
    "patient_id": "patient-001",
    "status": "processing",
    ...
  }
]
```

---

### 6. Get Patient Results

#### `GET /api/v1/results/{patient_id}`

Get analysis results for a patient.

**Path Parameters**:
- `patient_id`: Patient identifier

**Query Parameters**:
- `limit` (optional): Max results (1-50, default 10)
- `next_token` (optional): Pagination token

**Response**: `200 OK`
```json
{
  "patient_id": "patient-001",
  "total_results": 15,
  "results": [
    {
      "job_id": "job-abc123",
      "patient_id": "patient-001",
      "s3_key": "uploads/patient-001/...",
      "analyzed_at": "2024-01-15T12:05:30Z",
      "audio_emotion": {
        "primary_emotion": "calm",
        "confidence": 0.87,
        "all_emotions": [...]
      },
      "facial_emotion": {
        "primary_emotion": "neutral",
        "confidence": 0.82,
        ...
      },
      "compliance": {
        "pill_detected": true,
        "compliance_score": 0.95,
        ...
      },
      "multimodal_fusion": {
        "overall_emotion": "calm",
        "risk_level": "low",
        ...
      },
      "clinical_summary": {
        "emotional_state": "Patient appears calm and stable",
        "medication_adherence": "Compliant",
        "recommendations": [...]
      },
      "processing_time_seconds": 45.2
    }
  ],
  "next_token": "eyJw..."
}
```

---

### 7. Get Result by Job ID

#### `GET /api/v1/results/job/{job_id}`

Get analysis result for a specific job.

**Path Parameters**:
- `job_id`: Job identifier

**Response**: `200 OK`
```json
{
  "job_id": "job-abc123",
  "patient_id": "patient-001",
  ...
}
```

**Error Responses**:
- `404 Not Found`: No result found (job may still be processing)

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Resource doesn't exist |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error - Server-side error |

---

## Rate Limiting

- **Default**: 10 requests/second per IP
- **Burst**: Up to 20 requests
- **Response Header**: `X-RateLimit-Remaining`

When rate limited, you'll receive:
```json
{
  "error": "Too Many Requests",
  "status": 429
}
```

---

## Pagination

Endpoints that return lists support pagination:

1. **First Request**:
   ```
   GET /api/v1/results/patient-001?limit=10
   ```

2. **Response includes `next_token`**:
   ```json
   {
     "results": [...],
     "next_token": "eyJw..."
   }
   ```

3. **Next Page**:
   ```
   GET /api/v1/results/patient-001?limit=10&next_token=eyJw...
   ```

---

## Example Workflows

### Complete Analysis Workflow

```bash
# 1. Create job
curl -X POST http://localhost:8000/api/v1/analyze/ \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient-001",
    "filename": "checkin.mp4",
    "content_type": "video/mp4"
  }'

# Response: { "job_id": "job-abc123", "presigned_url": "https://..." }

# 2. Upload file to S3
curl -X PUT "https://s3.amazonaws.com/..." \
  -H "Content-Type: video/mp4" \
  --upload-file checkin.mp4

# 3. Poll job status
curl http://localhost:8000/api/v1/jobs/job-abc123/status

# 4. Get results when completed
curl http://localhost:8000/api/v1/results/patient-001
```

---

## OpenAPI/Swagger Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## SDK Examples

### Python

```python
import requests

# Create job
response = requests.post(
    "http://localhost:8000/api/v1/analyze/",
    json={
        "patient_id": "patient-001",
        "filename": "checkin.mp4",
        "content_type": "video/mp4"
    }
)
job = response.json()

# Upload to S3
with open("checkin.mp4", "rb") as f:
    requests.put(
        job["presigned_url"],
        data=f,
        headers={"Content-Type": "video/mp4"}
    )

# Poll status
import time
while True:
    status = requests.get(
        f"http://localhost:8000/api/v1/jobs/{job['job_id']}/status"
    ).json()
    
    if status["status"] in ["completed", "failed"]:
        break
    
    print(f"Progress: {status.get('progress', 0)}%")
    time.sleep(5)

# Get results
results = requests.get(
    f"http://localhost:8000/api/v1/results/{job['patient_id']}"
).json()
```

### JavaScript

```javascript
// Create job
const response = await fetch('http://localhost:8000/api/v1/analyze/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    patient_id: 'patient-001',
    filename: 'checkin.mp4',
    content_type: 'video/mp4'
  })
});
const job = await response.json();

// Upload to S3
await fetch(job.presigned_url, {
  method: 'PUT',
  headers: { 'Content-Type': 'video/mp4' },
  body: fileBlob
});

// Poll status
const pollStatus = async () => {
  const status = await fetch(
    `http://localhost:8000/api/v1/jobs/${job.job_id}/status`
  ).then(r => r.json());
  
  if (status.status === 'completed') {
    // Get results
    const results = await fetch(
      `http://localhost:8000/api/v1/results/${job.patient_id}`
    ).then(r => r.json());
    
    console.log(results);
  }
};
```

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/your-org/schizodot-ai-dot/issues
- Email: support@schizodot.ai
