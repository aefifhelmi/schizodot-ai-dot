from datetime import datetime, timezone
from typing import Optional
from app.core.aws import dynamodb
from app.core.config import settings

_table = None

def _table_handle():
    global _table
    if _table is None:
        _table = dynamodb().Table(settings.DYNAMO_TABLE)
    return _table

def write_upload_log(
    patient_id: str,
    s3_key: str,
    size_bytes: Optional[int] = None,
    media_type: Optional[str] = None,
):
    item = {
        "user_id": patient_id,                           # HASH
        "timestamp": datetime.now(timezone.utc).isoformat(),# RANGE
        "s3_key": s3_key,
        "size_bytes": size_bytes or 0,
        "media_type": media_type or "unknown",
        "status": "uploaded",
        "source": "local-dev",
    }
    _table_handle().put_item(Item=item)
    return item
