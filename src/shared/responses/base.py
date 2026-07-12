from typing import Generic, TypeVar, Optional, Any, List
from pydantic import Field
from datetime import datetime
from src.shared.base.schema import BaseSchema

T = TypeVar("T")

class ResponseSchema(BaseSchema, Generic[T]):
    """
    Định dạng Response chuẩn (Standard Response) cho mọi API thành công.
    Giúp Frontend luôn nhận được cùng một format: {success, message, data, path, timestamp}
    """
    success: bool = True
    message: str = "Thành công"
    data: Optional[T] = None
    path: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)

class ErrorResponseSchema(BaseSchema):
    """
    Định dạng Response chuẩn khi có lỗi.
    """
    success: bool = False
    message: str
    error_code: str
    details: Optional[Any] = None
    path: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)

class PaginationMetadata(BaseSchema):
    """
    Metadata cho phân trang dữ liệu.
    """
    total_items: int
    current_page: int
    page_size: int
    total_pages: int

class PaginatedResponseSchema(BaseSchema, Generic[T]):
    """
    Định dạng Response chuẩn cho các API trả về danh sách phân trang (List).
    """
    success: bool = True
    message: str = "Thành công"
    data: List[T]
    pagination: PaginationMetadata
    path: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)
