# app/api/v1/endpoints/analyze.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from app.services.presign_service import create_presigned_put_url, object_key
from app.services.log_service import write_upload_log

router = APIRouter()

class PresignResponse(BaseModel):
    url: str
    bucket: str
    key: str
    expires_in: int

@router.get("/presign/{patient_id}", response_model=PresignResponse, summary="Get S3 presigned PUT URL")
async def get_presigned_upload(
    patient_id: str,
    filename: str = Query(..., min_length=1, description="Original filename"),
    content_type: str = Query(..., min_length=1, description="MIME type, e.g. video/mp4 or audio/mpeg"),
):
    if not content_type.startswith(("video/", "audio/")):
        raise HTTPException(status_code=400, detail="Only audio/video content_type allowed")
    key = object_key(patient_id, filename)
    presigned = create_presigned_put_url(key, content_type)
    return presigned

class ConfirmBody(BaseModel):
    patient_id: str = Field(min_length=1)
    key: str = Field(min_length=3)
    size_bytes: Optional[int] = 0
    media_type: Optional[str] = None

@router.post("/confirm", summary="Confirm upload and log to DynamoDB")
async def confirm_upload(body: ConfirmBody):
    # In a real system, you might HEAD the object from S3 to verify existence/size.
    item = write_upload_log(
        patient_id=body.patient_id,
        s3_key=body.key,
        size_bytes=body.size_bytes,
        media_type=body.media_type,
    )
    return {"ok": True, "log": item}
