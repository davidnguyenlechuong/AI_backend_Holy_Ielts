from fastapi import APIRouter, HTTPException, Form, UploadFile, File
from src.modules.writing.schemas import WritingTask2Request
from src.modules.writing.service import evaluate_task1, evaluate_task2
from src.shared.responses.base import ResponseSchema
from typing import Optional

router = APIRouter(
    prefix="/writing",
    tags=["Writing"]
)

@router.post("/evaluate/task1", response_model=ResponseSchema)
async def evaluate_writing_task1(
    topic: str = Form(..., min_length=10, description="Đề bài IELTS Writing Task 1"),
    essay: str = Form(..., min_length=50, description="Bài viết của học viên"),
    image: UploadFile = File(..., description="Ảnh biểu đồ (Bắt buộc với Task 1)")
):
    """
    API chấm điểm bài thi IELTS Writing Task 1.
    Yêu cầu dữ liệu dưới dạng multipart/form-data.
    """
    try:
        image_bytes = await image.read()
        mime_type = image.content_type
        
        feedback = await evaluate_task1(
            topic=topic,
            essay=essay,
            image_bytes=image_bytes,
            mime_type=mime_type
        )
        return ResponseSchema(
            success=True,
            message="Chấm điểm IELTS Writing Task 1 thành công",
            data={"feedback": feedback}
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate/task2", response_model=ResponseSchema)
async def evaluate_writing_task2(request: WritingTask2Request):
    """
    API chấm điểm bài thi IELTS Writing Task 2.
    Yêu cầu dữ liệu dưới dạng application/json.
    """
    try:
        feedback = await evaluate_task2(
            topic=request.topic,
            essay=request.essay
        )
        return ResponseSchema(
            success=True,
            message="Chấm điểm IELTS Writing Task 2 thành công",
            data={"feedback": feedback}
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
