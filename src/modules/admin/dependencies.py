import uuid
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.db.dependencies import get_db
from src.core.security import decode_access_token
from src.models.auth import User
from src.shared.responses.base import ErrorResponseSchema, ErrorContent, ErrorDetails

bearer_scheme = HTTPBearer(auto_error=False)

UNAUTHORIZED_RESPONSE = {
    "success": False,
    "message": "Vui lòng đăng nhập lại",
    "messageCode": "UNAUTHORIZED",
}

FORBIDDEN_RESPONSE = {
    "success": False,
    "message": "Bạn không có quyền truy cập tính năng này",
    "messageCode": "FORBIDDEN_ACCESS",
}


async def _extract_token(
    credentials: HTTPAuthorizationCredentials | None,
    request: Request,
) -> str:
    """Lấy JWT từ Authorization header hoặc cookie access_token"""
    # Ưu tiên Bearer header
    if credentials and credentials.credentials:
        return credentials.credentials
    # Fallback lấy từ cookie
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=UNAUTHORIZED_RESPONSE,
    )


async def get_admin_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency bảo vệ tất cả endpoint /api/v1/admin/*.
    - 401 nếu chưa đăng nhập / token không hợp lệ
    - 403 nếu role != ADMIN
    """
    token = await _extract_token(credentials, request)

    # Giải mã JWT
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=UNAUTHORIZED_RESPONSE,
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=UNAUTHORIZED_RESPONSE,
        )

    # Query user từ DB
    try:
        result = await db.execute(select(User).filter(User.id == uuid.UUID(user_id)))
        user = result.scalars().first()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=UNAUTHORIZED_RESPONSE,
        )

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=UNAUTHORIZED_RESPONSE,
        )

    # Kiểm tra quyền admin
    if user.role.upper() != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=FORBIDDEN_RESPONSE,
        )

    return user
