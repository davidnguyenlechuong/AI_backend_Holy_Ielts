from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from src.modules.admin.dependencies import get_admin_user
from src.integrations.storage.storage_service import upload_file_to_storage
from src.shared.responses.base import ResponseSchema
from src.models.auth import User

router = APIRouter(
    prefix="/uploads",
    tags=["Uploads"]
)

# Allowed image MIME types
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
}

# Maximum file size: 5MB
MAX_FILE_SIZE = 5 * 1024 * 1024

@router.post("/image", response_model=ResponseSchema, status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    admin_user: User = Depends(get_admin_user)
):
    """
    Upload an image for question bank/exams or general usage.
    Only allowed for Admins.
    - Supported formats: jpg, jpeg, png, gif, webp
    - Maximum size: 5MB
    """
    # 1. Validate file extension and MIME type
    mime_type = file.content_type or "image/jpeg"
    if mime_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": f"Định dạng file {mime_type} không hợp lệ. Chỉ chấp nhận JPEG, PNG, GIF, WEBP.",
                "messageCode": "INVALID_FILE_TYPE"
            }
        )
        
    # 2. Validate file size
    # We read a chunk to inspect size without loading entire file into memory if it's huge
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": f"Kích thước file vượt quá giới hạn cho phép (tối đa {MAX_FILE_SIZE // (1024*1024)}MB).",
                "messageCode": "FILE_TOO_LARGE"
            }
        )
        
    try:
        # 3. Upload to storage
        url = await upload_file_to_storage(
            file_bytes=content,
            filename=file.filename or "upload.png",
            mime_type=mime_type
        )
        
        # 4. Return standard response
        return ResponseSchema(
            success=True,
            message="Tải ảnh lên thành công",
            data={"url": url}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": f"Lỗi tải ảnh lên storage: {str(e)}",
                "messageCode": "UPLOAD_FAILED"
            }
        )
