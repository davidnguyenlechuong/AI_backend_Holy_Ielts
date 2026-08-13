from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class SpeakingEvaluationFeedback(BaseModel):
    feedback: Dict[str, Any] = Field(..., description="Chi tiết nhận xét từ AI, bao gồm điểm số và nhận xét các tiêu chí (FC, LR, GRA, PR)")

class SpeakingEvaluationRequest(BaseModel):
    """
    Schema này chủ yếu dùng cho documentation.
    Thực tế API Speaking sử dụng `Form` và `UploadFile` (multipart/form-data) 
    do yêu cầu upload file audio, nên không thể map trực tiếp với JSON Request body bằng BaseModel.
    """
    question: Optional[str] = Field(None, description="Câu hỏi Speaking (Part 1, 3)")
    cue_card: Optional[str] = Field(None, description="Đề bài Cue Card (Part 2)")
