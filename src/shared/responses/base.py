import uuid
from typing import Generic, TypeVar, Optional, Any, List, Dict, Union
from pydantic import Field
from datetime import datetime, timezone
from src.shared.base.schema import BaseSchema

T = TypeVar("T")

def get_iso_timestamp() -> str:
    # Trả về định dạng ISO 8601 chuẩn UTC (kết thúc bằng Z)
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

def get_uuid() -> str:
    return str(uuid.uuid4())

class PaginationMetadata(BaseSchema):
    """
    Metadata cho phân trang dữ liệu, khớp với frontend 'metadata'.
    """
    page: int
    limit: int
    total: int
    totalPages: int
    nextPage: Optional[int] = None
    prevPage: Optional[int] = None

class ResponseSchema(BaseSchema, Generic[T]):
    """
    Định dạng Response chuẩn (Standard Response) cho mọi API thành công.
    Khớp 1:1 với Frontend interface 'ApiResponse'
    """
    success: bool = True
    message: str = "Thành công"
    requestId: str = Field(default_factory=get_uuid)
    timestamp: str = Field(default_factory=get_iso_timestamp)
    data: Optional[T] = None
    metadata: Optional[PaginationMetadata] = None

class ErrorDetails(BaseSchema):
    field: str
    message: Optional[str] = None

class ErrorContent(BaseSchema):
    details: Union[List[ErrorDetails], str]

class ErrorResponseSchema(BaseSchema):
    """
    Định dạng Response chuẩn khi có lỗi.
    Khớp 1:1 với Frontend interface 'ApiError'.
    """
    success: bool = False
    message: str
    requestId: str = Field(default_factory=get_uuid)
    timestamp: str = Field(default_factory=get_iso_timestamp)
    messageCode: str
    error: Optional[ErrorContent] = None
    path: str = ""

class PaginatedResponseSchema(BaseSchema, Generic[T]):
    """
    (Deprecated) Có thể dùng chung ResponseSchema thay thế, 
    nhưng giữ lại nếu có API đang map list tĩnh.
    """
    success: bool = True
    message: str = "Thành công"
    requestId: str = Field(default_factory=get_uuid)
    timestamp: str = Field(default_factory=get_iso_timestamp)
    data: List[T]
    metadata: PaginationMetadata

