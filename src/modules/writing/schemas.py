from pydantic import BaseModel, Field

class WritingTask2Request(BaseModel):
    topic: str = Field(..., min_length=10, description="Đề bài IELTS Writing cần ít nhất 10 ký tự")
    essay: str = Field(..., min_length=250, description="Bài viết của học viên cần ít nhất 250 ký tự")
