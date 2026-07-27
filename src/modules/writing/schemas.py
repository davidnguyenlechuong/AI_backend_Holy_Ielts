from pydantic import BaseModel, Field
from typing import Optional

class WritingTask2Request(BaseModel):
    topic: str = Field(..., min_length=10, max_length=500, description="Đề bài IELTS Writing (ít nhất 10 ký tự, tối đa 500 ký tự)")
    essay: str = Field(..., min_length=250, max_length=5000, description="Bài viết của học viên (ít nhất 250 ký tự, tối đa 5000 ký tự)")
    target_band: Optional[float] = Field(0.0, description="Điểm band mục tiêu")
    feedback_language: Optional[str] = Field("vi", description="Ngôn ngữ nhận xét: 'vi' hoặc 'en'")
