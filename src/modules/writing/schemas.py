from pydantic import BaseModel, Field

class WritingEvaluationRequest(BaseModel):
    topic: str = Field(..., min_length=10, max_length=500, description="Đề bài IELTS Writing (ít nhất 10 ký tự, tối đa 500 ký tự)")
    essay: str = Field(..., min_length=50, max_length=5000, description="Bài viết của học viên (ít nhất 50 ký tự, tối đa 5000 ký tự)")
