import json
from fastapi import APIRouter, HTTPException, Form, UploadFile, File
from fastapi.responses import StreamingResponse
from src.modules.writing.schemas import WritingTask2Request
from src.modules.writing.service import (
    evaluate_task1,
    evaluate_task2,
    evaluate_task1_stream,
    evaluate_task2_stream,
)
from src.shared.responses.base import ResponseSchema
from src.shared.utils.json_extractor import parse_ai_json_response
from typing import AsyncIterator, Optional

router = APIRouter(
    prefix="/writing",
    tags=["Writing"]
)

SSE_HEADERS = {"X-Accel-Buffering": "no", "Cache-Control": "no-cache"}


async def _sse_event_generator(chunk_generator: AsyncIterator[str]) -> AsyncIterator[str]:
    """
    Bọc 1 generator sinh text thô (từ AI provider) thành luồng SSE:
    - mỗi chunk text -> 1 event "chunk"
    - khi generator kết thúc -> parse JSON từ toàn bộ text đã gom -> 1 event "done"
    - nếu có lỗi bất kỳ lúc nào -> 1 event "error", không raise ra ngoài StreamingResponse
    """
    accumulated = ""
    try:
        async for chunk in chunk_generator:
            accumulated += chunk
            yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"

        feedback = parse_ai_json_response(accumulated)
        yield f"data: {json.dumps({'type': 'done', 'feedback': feedback})}\n\n"
    except HTTPException as he:
        yield f"data: {json.dumps({'type': 'error', 'message': str(he.detail)})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

@router.post("/evaluate/task1", response_model=ResponseSchema)
async def evaluate_writing_task1(
    topic: str = Form(..., min_length=10, description="Đề bài IELTS Writing Task 1"),
    essay: str = Form(..., min_length=50, description="Bài viết của học viên"),
    image: UploadFile = File(..., description="Ảnh biểu đồ (Bắt buộc với Task 1)"),
    target_band: float = Form(0.0, description="Điểm band mục tiêu"),
    feedback_language: str = Form("vi", description="Ngôn ngữ nhận xét: vi hoặc en")
):
    """
    API chấm điểm bài thi IELTS Writing Task 1.
    Yêu cầu dữ liệu dưới dạng multipart/form-data.
    """
    try:
        image_bytes = await image.read()
        mime_type = image.content_type
        if mime_type is None:
            raise HTTPException(status_code=400, detail="Could not determine image mime type")

        feedback = await evaluate_task1(
            topic=topic,
            essay=essay,
            image_bytes=image_bytes,
            mime_type=mime_type,
            target_band=target_band,
            feedback_language=feedback_language
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

@router.post("/evaluate/task1/stream")
async def evaluate_writing_task1_stream(
    topic: str = Form(..., min_length=10, description="Đề bài IELTS Writing Task 1"),
    essay: str = Form(..., min_length=50, description="Bài viết của học viên"),
    image: UploadFile = File(..., description="Ảnh biểu đồ (Bắt buộc với Task 1)"),
    target_band: float = Form(0.0, description="Điểm band mục tiêu"),
    feedback_language: str = Form("vi", description="Ngôn ngữ nhận xét: vi hoặc en")
):
    """
    API chấm điểm bài thi IELTS Writing Task 1, trả về dạng Server-Sent Events (SSE).
    """
    image_bytes = await image.read()
    mime_type = image.content_type
    if mime_type is None:
        raise HTTPException(status_code=400, detail="Could not determine image mime type")

    generator = evaluate_task1_stream(
        topic=topic,
        essay=essay,
        image_bytes=image_bytes,
        mime_type=mime_type,
        target_band=target_band,
        feedback_language=feedback_language
    )
    return StreamingResponse(_sse_event_generator(generator), media_type="text/event-stream", headers=SSE_HEADERS)

@router.post("/evaluate/task2", response_model=ResponseSchema)
async def evaluate_writing_task2(request: WritingTask2Request):
    """
    API chấm điểm bài thi IELTS Writing Task 2.
    Yêu cầu dữ liệu dưới dạng application/json.
    """
    try:
        feedback = await evaluate_task2(
            topic=request.topic,
            essay=request.essay,
            target_band=request.target_band if request.target_band is not None else 0.0,
            feedback_language=request.feedback_language if request.feedback_language is not None else "vi"
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

@router.post("/evaluate/task2/stream")
async def evaluate_writing_task2_stream(request: WritingTask2Request):
    """
    API chấm điểm bài thi IELTS Writing Task 2, trả về dạng Server-Sent Events (SSE).
    """
    generator = evaluate_task2_stream(
        topic=request.topic,
        essay=request.essay,
        target_band=request.target_band if request.target_band is not None else 0.0,
        feedback_language=request.feedback_language if request.feedback_language is not None else "vi"
    )
    return StreamingResponse(_sse_event_generator(generator), media_type="text/event-stream", headers=SSE_HEADERS)
