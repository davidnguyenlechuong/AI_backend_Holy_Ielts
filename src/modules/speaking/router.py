from fastapi import APIRouter, HTTPException, Form, UploadFile, File
from src.modules.speaking.service import evaluate_part1, evaluate_part2, evaluate_part3
from src.shared.responses.base import ResponseSchema

router = APIRouter(
    prefix="/speaking",
    tags=["Speaking"]
)

@router.post("/evaluate/part1", response_model=ResponseSchema)
async def evaluate_speaking_part1(
    question: str = Form(..., description="Câu hỏi Part 1"),
    audio: UploadFile = File(..., description="File ghi âm câu trả lời")
):
    try:
        audio_bytes = await audio.read()
        mime_type = audio.content_type
        
        feedback = await evaluate_part1(
            question=question,
            audio_bytes=audio_bytes,
            mime_type=mime_type
        )
        return ResponseSchema(
            success=True,
            message="Chấm điểm IELTS Speaking Part 1 thành công",
            data={"feedback": feedback}
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate/part2", response_model=ResponseSchema)
async def evaluate_speaking_part2(
    cue_card: str = Form(..., description="Đề bài Cue Card Part 2"),
    audio: UploadFile = File(..., description="File ghi âm câu trả lời")
):
    try:
        audio_bytes = await audio.read()
        mime_type = audio.content_type
        
        feedback = await evaluate_part2(
            cue_card=cue_card,
            audio_bytes=audio_bytes,
            mime_type=mime_type
        )
        return ResponseSchema(
            success=True,
            message="Chấm điểm IELTS Speaking Part 2 thành công",
            data={"feedback": feedback}
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate/part3", response_model=ResponseSchema)
async def evaluate_speaking_part3(
    question: str = Form(..., description="Câu hỏi Part 3"),
    audio: UploadFile = File(..., description="File ghi âm câu trả lời")
):
    try:
        audio_bytes = await audio.read()
        mime_type = audio.content_type
        
        feedback = await evaluate_part3(
            question=question,
            audio_bytes=audio_bytes,
            mime_type=mime_type
        )
        return ResponseSchema(
            success=True,
            message="Chấm điểm IELTS Speaking Part 3 thành công",
            data={"feedback": feedback}
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
