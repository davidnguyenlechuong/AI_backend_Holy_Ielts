from fastapi import APIRouter, Request
from src.modules.writing.schemas import WritingEvaluationRequest
from src.modules.writing.service import evaluate_writing_essay
from src.shared.responses.base import ResponseSchema
from typing import Dict, Any

router = APIRouter(prefix="/writing", tags=["Writing AI"])

@router.post("/evaluate", response_model=ResponseSchema[Dict[str, Any]])
async def evaluate_essay(request: Request, payload: WritingEvaluationRequest):
    # Gọi AI để chấm điểm
    feedback = await evaluate_writing_essay(payload.topic, payload.essay)
    
    return ResponseSchema(
        success=True,
        message="Chấm điểm IELTS Writing thành công",
        data={"feedback": feedback},
        path=request.url.path
    )
