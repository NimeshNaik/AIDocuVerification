from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import Response

from app.core.security import get_current_user
from app.services.upscaler import upscaler

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upscale")
async def upscale_document(
    file: UploadFile = File(...),
    current_officer: dict = Depends(get_current_user)
):
    """
    Enhance a document image using Swin2SR upscaling (4x).
    Returns the upscaled image as JPEG.
    """
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG and PNG images are supported for upscaling"
        )
    
    try:
        content = await file.read()
        upscaled_bytes = upscaler.upscale_image(content)
        
        return Response(content=upscaled_bytes, media_type="image/jpeg")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upscaling failed: {str(e)}"
        )
