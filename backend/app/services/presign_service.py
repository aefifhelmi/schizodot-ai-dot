# app/services/presign_service.py
from datetime import datetime, timezone, timedelta
from urllib.parse import quote
from app.core.aws import s3
from app.core.config import settings

def object_key(patient_id: str, filename: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe = quote(filename, safe="._-")
    return f"uploads/{patient_id}/{ts}_{safe}"

def create_presigned_put_url(key: str, content_type: str, expires_seconds: int = 900) -> dict:
    client = s3()
    url = client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": settings.S3_BUCKET,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=expires_seconds,
    )
    return {"url": url, "bucket": settings.S3_BUCKET, "key": key, "expires_in": expires_seconds}
