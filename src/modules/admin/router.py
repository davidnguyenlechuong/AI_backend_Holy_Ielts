"""
Admin Router — CRUD Endpoints cho Question Bank & Full Exam
Yêu cầu Admin role được guard tự động ở Router-level dependency.
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.dependencies import get_db
from src.modules.admin.dependencies import get_admin_user
from src.modules.admin.service import AdminQuestionService, AdminExamService
from src.modules.admin.schemas import (
    CreateIeltsQuestionRequest,
    UpdateIeltsQuestionRequest,
    CreateIeltsExamRequest,
    UpdateIeltsExamRequest,
)
from src.shared.responses.base import ResponseSchema

# Áp dụng check role Admin cho TOÀN BỘ routes trong controller này
router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(get_admin_user)]
)


# ══════════════════════════════════════════════════════════════════════════════
# QUESTION BANK — /api/v1/admin/tests
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/tests", response_model=ResponseSchema, status_code=status.HTTP_200_OK)
async def list_questions(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    skill: Optional[str] = Query(None, description="WRITING | SPEAKING"),
    part: Optional[str] = Query(None, description="TASK_1 | TASK_2 | PART_1 | PART_2 | PART_3"),
    questionType: Optional[str] = Query(None, description="bar_chart | agree_disagree | describe_person | ..."),
    db: AsyncSession = Depends(get_db),
):
    """
    Lấy danh sách câu hỏi trong Question Bank.
    Filter 3 cấp: **skill** → **part** → **questionType**.
    """
    svc = AdminQuestionService(db)
    data = await svc.get_questions(
        page=page, page_size=pageSize,
        skill=skill, part=part, question_type=questionType,
    )
    return ResponseSchema(success=True, message="Thành công", data=data)


@router.post("/tests", response_model=ResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_question(
    body: CreateIeltsQuestionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Tạo mới câu hỏi trong Question Bank.

    - `skill`: **WRITING** | **SPEAKING**
    - `part`: **TASK_1** | **TASK_2** | **PART_1** | **PART_2** | **PART_3**
    - `questionType`: dạng đề (validate theo skill+part)
    - `imageUrl`: optional (dùng cho Writing Task 1)
    - `bulletPoints`: optional array (dùng cho Speaking Part 2)
    """
    svc = AdminQuestionService(db)
    q = await svc.create_question(body)
    return ResponseSchema(success=True, message="Tạo câu hỏi thành công", data=q)


@router.put("/tests/{question_id}", response_model=ResponseSchema, status_code=status.HTTP_200_OK)
async def update_question(
    question_id: uuid.UUID,
    body: UpdateIeltsQuestionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Cập nhật toàn bộ thông tin câu hỏi (full override)."""
    svc = AdminQuestionService(db)
    updated = await svc.update_question(question_id, body)
    return ResponseSchema(success=True, message="Cập nhật câu hỏi thành công", data=updated)


@router.delete("/tests/{question_id}", response_model=ResponseSchema, status_code=status.HTTP_200_OK)
async def delete_question(
    question_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Xóa câu hỏi. Response `data: null`, FE check `success === true`."""
    svc = AdminQuestionService(db)
    await svc.delete_question(question_id)
    return ResponseSchema(success=True, message="Xóa câu hỏi thành công", data=None)


# ══════════════════════════════════════════════════════════════════════════════
# FULL EXAM — /api/v1/admin/exams
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/exams", response_model=ResponseSchema, status_code=status.HTTP_200_OK)
async def list_exams(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Lấy danh sách Full Exam (bao gồm cả Draft và Published)."""
    svc = AdminExamService(db)
    data = await svc.get_exams(page=page, page_size=pageSize, published_only=False)
    return ResponseSchema(success=True, message="Thành công", data=data)


@router.post("/exams", response_model=ResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_exam(
    body: CreateIeltsExamRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Tạo Full Exam gom nhiều câu hỏi lại theo thứ tự.

    Body example:
    ```json
    {
      "title": "Full Practice — Writing",
      "isPublished": false,
      "questions": [
        {"questionId": "uuid-1", "orderIndex": 1},
        {"questionId": "uuid-2", "orderIndex": 2}
      ]
    }
    ```
    """
    svc = AdminExamService(db)
    exam = await svc.create_exam(body, db)
    return ResponseSchema(success=True, message="Tạo đề tổng hợp thành công", data=exam)


@router.put("/exams/{exam_id}", response_model=ResponseSchema, status_code=status.HTTP_200_OK)
async def update_exam(
    exam_id: uuid.UUID,
    body: UpdateIeltsExamRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Cập nhật Full Exam.
    Danh sách `questions` sẽ được **thay thế hoàn toàn** (replace, không merge).
    """
    svc = AdminExamService(db)
    updated = await svc.update_exam(exam_id, body, db)
    return ResponseSchema(success=True, message="Cập nhật đề tổng hợp thành công", data=updated)


@router.delete("/exams/{exam_id}", response_model=ResponseSchema, status_code=status.HTTP_200_OK)
async def delete_exam(
    exam_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Xóa Full Exam (cascade xóa cả join records)."""
    svc = AdminExamService(db)
    await svc.delete_exam(exam_id)
    return ResponseSchema(success=True, message="Xóa đề tổng hợp thành công", data=None)
