"""
Practice Router — Student-facing APIs cho Question Bank & Full Exam
Học viên browse câu hỏi/đề thi qua Service/Repository dùng chung.
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.dependencies import get_db
from src.models.auth import User
from src.modules.auth.dependencies import get_current_user
from src.modules.admin.schemas import IeltsQuestionResponse, IeltsExamResponse
from src.modules.admin.repository import IeltsQuestionRepository, IeltsExamRepository
from src.modules.admin.service import AdminExamService
from src.models.ielts import IeltsAttempt
from src.shared.responses.base import ResponseSchema
from src.shared.base.schema import BaseSchema
from pydantic import Field
from datetime import datetime, timezone
from sqlalchemy import select

class SubmitAttemptRequest(BaseSchema):
    answerText: Optional[str] = None   # Writing / Speaking transcript
    audioUrl: Optional[str] = None     # Speaking audio URL


class AttemptResponse(BaseSchema):
    id: uuid.UUID
    status: str
    questionId: Optional[uuid.UUID] = Field(None, alias="question_id")
    examId: Optional[uuid.UUID] = Field(None, alias="exam_id")
    startedAt: str = Field(alias="started_at")
    submittedAt: Optional[str] = Field(None, alias="submitted_at")

    @classmethod
    def from_orm_obj(cls, attempt: IeltsAttempt):
        def fmt(dt):
            if dt is None:
                return None
            return dt.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        return cls.model_validate({
            "id": attempt.id,
            "status": attempt.status,
            "question_id": attempt.question_id,
            "exam_id": attempt.exam_id,
            "started_at": fmt(attempt.started_at),
            "submitted_at": fmt(attempt.submitted_at),
        })

    model_config = {"from_attributes": True, "populate_by_name": True}


router = APIRouter(prefix="/practice", tags=["Practice"])


# ─────────────────────────────────────────────────────────────────────────────
# GET /practice/questions — Browse Question Bank (Public)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/questions", response_model=ResponseSchema, status_code=status.HTTP_200_OK)
async def browse_questions(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    skill: Optional[str] = Query(None, description="WRITING | SPEAKING"),
    part: Optional[str] = Query(None, description="TASK_1 | TASK_2 | PART_1 | PART_2 | PART_3"),
    questionType: Optional[str] = Query(None, description="bar_chart / agree_disagree..."),
    db: AsyncSession = Depends(get_db),
):
    """Browse câu hỏi. Gọi qua QuestionRepository dùng chung."""
    repo = IeltsQuestionRepository(db)
    items, total = await repo.get_list(
        page=page, page_size=pageSize,
        skill=skill, part=part, question_type=questionType
    )
    return ResponseSchema(
        success=True,
        message="Thành công",
        data={
            "items": [IeltsQuestionResponse.model_validate(q) for q in items],
            "total": total,
            "page": page,
            "pageSize": pageSize,
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /practice/exams — Browse Full Exams (Only Published)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/exams", response_model=ResponseSchema, status_code=status.HTTP_200_OK)
async def browse_exams(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Browse đề thi. 
    Tái sử dụng ExamRepository với tham số `published_only=True` để ẩn các đề nháp.
    """
    repo = IeltsExamRepository(db)
    exam_svc = AdminExamService(db) # Dùng helper _build_exam_response của service để map data

    # Chỉ quét các đề đã publish
    exams, total = await repo.get_list(page=page, page_size=pageSize, published_only=True)
    
    items = []
    for exam in exams:
        # Load đầy đủ câu hỏi liên kết trong đề
        full_exam = await repo.get_by_id(exam.id)
        if full_exam:
            items.append(exam_svc._build_exam_response(full_exam))

    return ResponseSchema(
        success=True,
        message="Thành công",
        data={
            "items": items,
            "total": total,
            "page": page,
            "pageSize": pageSize,
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /practice/questions/:id/attempt — Bắt đầu làm câu đơn lẻ (Auth)
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/questions/{question_id}/attempt",
    response_model=ResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def start_question_attempt(
    question_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = IeltsQuestionRepository(db)
    question = await repo.get_by_id(question_id)
    if not question:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Câu hỏi không tồn tại")

    attempt = IeltsAttempt(
        user_id=current_user.id,
        question_id=question_id,
        exam_id=None,
        status="IN_PROGRESS",
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)

    return ResponseSchema(
        success=True,
        message="Bắt đầu làm bài thành công",
        data=AttemptResponse.from_orm_obj(attempt),
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /practice/exams/:id/attempt — Bắt đầu làm Full Exam (Auth)
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/exams/{exam_id}/attempt",
    response_model=ResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def start_exam_attempt(
    exam_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = IeltsExamRepository(db)
    exam = await repo.get_by_id(exam_id)
    if not exam or not exam.is_published:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Đề thi không tồn tại hoặc chưa được xuất bản")

    attempt = IeltsAttempt(
        user_id=current_user.id,
        question_id=None,
        exam_id=exam_id,
        status="IN_PROGRESS",
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)

    return ResponseSchema(
        success=True,
        message="Bắt đầu làm đề thành công",
        data=AttemptResponse.from_orm_obj(attempt),
    )


# ─────────────────────────────────────────────────────────────────────────────
# PUT /practice/attempts/:id/submit — Nộp bài (Auth)
# ─────────────────────────────────────────────────────────────────────────────

@router.put(
    "/attempts/{attempt_id}/submit",
    response_model=ResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def submit_attempt(
    attempt_id: uuid.UUID,
    body: SubmitAttemptRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(IeltsAttempt).where(
            IeltsAttempt.id == attempt_id,
            IeltsAttempt.user_id == current_user.id,
        )
    )
    attempt = result.scalars().first()
    if not attempt:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Bài làm không tồn tại")
    if attempt.status != "IN_PROGRESS":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Bài làm đã được nộp trước đó")

    attempt.status = "SUBMITTED"
    setattr(attempt, "answer_text", body.answerText)
    setattr(attempt, "audio_url", body.audioUrl)
    attempt.submitted_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(attempt)

    return ResponseSchema(
        success=True,
        message="Nộp bài thành công",
        data=AttemptResponse.from_orm_obj(attempt),
    )
