from fastapi import APIRouter
router = APIRouter()

@router.get("/", summary="Health")
async def health_check():
    return {"status": "ok"}
