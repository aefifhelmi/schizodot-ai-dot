from typing import Dict
from datetime import datetime, timezone
from urllib.parse import quote_plus
from app.core.aws import s3
from app.core.config import settings

def build_key(patient_id: str, filename: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    # keep it tidy in uploads/
    return f"uploads/{patient_id}/{ts}_{filename}"

def presign_put(patient_id: str, filename: str, content_type: str, expires_in: int = 900) -> Dict[str, str]:
    key = build_key(patient_id, filename)
    url = s3().generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": settings.S3_BUCKET,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=expires_in,
    )
    return {"url": url, "bucket": settings.S3_BUCKET, "key": key, "expires_in": expires_in}
