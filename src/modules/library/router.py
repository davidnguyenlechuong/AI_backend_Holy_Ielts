import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import joinedload

from src.db.dependencies import get_db
from src.core.security import decode_access_token
from src.models.auth import User
from src.models.ielts import Exam, ExamQuestion, ExamAttempt, Tag, Topic
from src.modules.auth.dependencies import get_current_user
from src.shared.responses.base import ResponseSchema, PaginationMetadata
from src.modules.library.schemas import (
    ExamResponseSchema,
    TagResponseSchema,
    ExamAttemptResponseSchema,
    ExamAttemptDetailResponseSchema,
)


router = APIRouter(prefix="/library", tags=["Library"])

bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    if credentials is None:
        return None

    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    try:
        result = await db.execute(select(User).filter(User.id == uuid.UUID(user_id)))
        return result.scalars().first()
    except Exception:
        return None

@router.get("/exams", response_model=ResponseSchema)
async def get_exams(
    skill: str = Query(..., description="WRITING, SPEAKING, READING, LISTENING"),
    tag_code: Optional[str] = Query(None),
    task_type: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    topic: Optional[str] = Query(None, description="Topic slug name"),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    query = select(Exam).where(Exam.skill == skill.upper())

    if tag_code:
        query = query.join(Exam.tags).where(Tag.code == tag_code)

    if task_type:
        query = query.where(Exam.task_type == task_type.upper())

    if difficulty:
        query = query.where(Exam.difficulty == difficulty.upper())

    if topic:
        query = query.join(Exam.topic).where(Topic.slug == topic.lower())

    if search:
        query = query.where(
            (Exam.title.ilike(f"%{search}%")) | (Exam.description.ilike(f"%{search}%"))
        )

    # Clone query to get total count
    count_query = select(func.count()).select_from(query.distinct().subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # Apply pagination and options
    query = query.options(
        joinedload(Exam.tags),
        joinedload(Exam.topic),
        joinedload(Exam.questions)
    )

    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    exams = result.unique().scalars().all()

    exams_list = []
    for exam in exams:
        # Fetch attempt count
        attempt_count_res = await db.execute(
            select(func.count(ExamAttempt.id)).where(ExamAttempt.exam_id == exam.id)
        )
        attempt_count = attempt_count_res.scalar() or 0

        # Check completion
        is_completed = False
        if current_user:
            is_completed_res = await db.execute(
                select(func.count(ExamAttempt.id)).where(
                    ExamAttempt.exam_id == exam.id,
                    ExamAttempt.user_id == current_user.id
                )
            )
            is_completed = (is_completed_res.scalar() or 0) > 0

        exam_dict = {
            "id": exam.id,
            "title": exam.title,
            "skill": exam.skill,
            "task_type": exam.task_type,
            "difficulty": exam.difficulty,
            "duration_minutes": exam.duration_minutes,
            "topic": exam.topic,
            "tags": exam.tags,
            "questions": exam.questions,
            "is_completed": is_completed,
            "attempt_count": attempt_count
        }
        exams_list.append(ExamResponseSchema.model_validate(exam_dict))

    total_pages = (total + limit - 1) // limit
    next_page = page + 1 if page < total_pages else None
    prev_page = page - 1 if page > 1 else None

    return ResponseSchema(
        success=True,
        message="Thành công",
        data=exams_list,
        metadata=PaginationMetadata(
            page=page,
            limit=limit,
            total=total,
            totalPages=total_pages,
            nextPage=next_page,
            prevPage=prev_page
        )
    )

@router.get("/exams/{exam_id}", response_model=ResponseSchema)
async def get_exam_detail(
    exam_id: uuid.UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    query = select(Exam).where(Exam.id == exam_id).options(
        joinedload(Exam.tags),
        joinedload(Exam.topic),
        joinedload(Exam.questions)
    )
    result = await db.execute(query)
    exam = result.unique().scalars().first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Fetch attempt count
    attempt_count_res = await db.execute(
        select(func.count(ExamAttempt.id)).where(ExamAttempt.exam_id == exam.id)
    )
    attempt_count = attempt_count_res.scalar() or 0

    # Check completion
    is_completed = False
    if current_user:
        is_completed_res = await db.execute(
            select(func.count(ExamAttempt.id)).where(
                ExamAttempt.exam_id == exam.id,
                ExamAttempt.user_id == current_user.id
            )
        )
        is_completed = (is_completed_res.scalar() or 0) > 0

    exam_dict = {
        "id": exam.id,
        "title": exam.title,
        "skill": exam.skill,
        "task_type": exam.task_type,
        "difficulty": exam.difficulty,
        "duration_minutes": exam.duration_minutes,
        "topic": exam.topic,
        "tags": exam.tags,
        "questions": exam.questions,
        "is_completed": is_completed,
        "attempt_count": attempt_count
    }

    return ResponseSchema(
        success=True,
        message="Thành công",
        data=ExamResponseSchema.model_validate(exam_dict)
    )

@router.post("/exams/{exam_id}/attempts", response_model=ResponseSchema)
async def start_exam_attempt(
    exam_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Exam).filter(Exam.id == exam_id))
    exam = result.scalars().first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    new_attempt = ExamAttempt(
        exam_id=exam_id,
        user_id=user.id,
        status="IN_PROGRESS"
    )
    db.add(new_attempt)
    await db.commit()
    await db.refresh(new_attempt)

    return ResponseSchema(
        success=True,
        message="Bắt đầu làm đề thành công",
        data={
            "attempt_id": str(new_attempt.id),
            "exam_id": str(new_attempt.exam_id),
            "started_at": new_attempt.started_at.isoformat().replace("+00:00", "Z"),
            "status": new_attempt.status
        }
    )

@router.get("/tags", response_model=ResponseSchema)
async def get_tags(
    skill: Optional[str] = Query(None, description="READING, LISTENING, WRITING, SPEAKING"),
    db: AsyncSession = Depends(get_db)
):
    query = select(Tag)
    if skill:
        query = query.where(Tag.skill == skill.upper())
    result = await db.execute(query)
    tags = result.scalars().all()

    return ResponseSchema(
        success=True,
        message="Thành công",
        data=[TagResponseSchema.model_validate(tag) for tag in tags]
    )


@router.get("/attempts", response_model=ResponseSchema)
async def get_library_attempts(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    skill: Optional[str] = Query(None, description="READING, LISTENING, WRITING, SPEAKING"),
    status: Optional[str] = Query(None, description="IN_PROGRESS, SUBMITTED"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lấy danh sách lượt làm đề thi Library (ExamAttempt) của user hiện tại.
    """
    query = select(ExamAttempt).where(ExamAttempt.user_id == user.id)

    if status:
        query = query.where(ExamAttempt.status == status.upper())

    if skill:
        query = query.join(ExamAttempt.exam).where(Exam.skill == skill.upper())

    # Count total first
    count_query = select(func.count()).select_from(query.distinct().subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # Sắp xếp và phân trang
    query = query.order_by(ExamAttempt.started_at.desc())
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    # Load Eagerly the relationships to avoid lazy load issues
    query = query.options(
        joinedload(ExamAttempt.exam).joinedload(Exam.tags),
        joinedload(ExamAttempt.exam).joinedload(Exam.topic),
        joinedload(ExamAttempt.exam).joinedload(Exam.questions)
    )

    result = await db.execute(query)
    attempts = result.unique().scalars().all()

    attempts_list = []
    for att in attempts:
        # Check completion
        is_completed = False
        is_completed_res = await db.execute(
            select(func.count(ExamAttempt.id)).where(
                ExamAttempt.exam_id == att.exam.id,
                ExamAttempt.user_id == user.id
            )
        )
        is_completed = (is_completed_res.scalar() or 0) > 0

        # Attempt count
        attempt_count_res = await db.execute(
            select(func.count(ExamAttempt.id)).where(ExamAttempt.exam_id == att.exam.id)
        )
        attempt_count = attempt_count_res.scalar() or 0

        exam_dict = {
            "id": att.exam.id,
            "title": att.exam.title,
            "skill": att.exam.skill,
            "task_type": att.exam.task_type,
            "difficulty": att.exam.difficulty,
            "duration_minutes": att.exam.duration_minutes,
            "topic": att.exam.topic,
            "tags": att.exam.tags,
            "questions": att.exam.questions,
            "is_completed": is_completed,
            "attempt_count": attempt_count
        }

        attempts_list.append(
            ExamAttemptDetailResponseSchema.model_validate({
                "id": att.id,
                "exam_id": att.exam_id,
                "status": att.status,
                "started_at": att.started_at,
                "submitted_at": att.submitted_at,
                "exam": exam_dict
            })
        )

    total_pages = (total + limit - 1) // limit
    next_page = page + 1 if page < total_pages else None
    prev_page = page - 1 if page > 1 else None

    return ResponseSchema(
        success=True,
        message="Thành công",
        data=attempts_list,
        metadata=PaginationMetadata(
            page=page,
            limit=limit,
            total=total,
            totalPages=total_pages,
            nextPage=next_page,
            prevPage=prev_page
        )
    )


@router.get("/attempts/{attempt_id}", response_model=ResponseSchema)
async def get_library_attempt_detail(
    attempt_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lấy chi tiết một lượt làm đề thi Library (ExamAttempt).
    """
    query = select(ExamAttempt).where(
        ExamAttempt.id == attempt_id,
        ExamAttempt.user_id == user.id
    ).options(
        joinedload(ExamAttempt.exam).joinedload(Exam.tags),
        joinedload(ExamAttempt.exam).joinedload(Exam.topic),
        joinedload(ExamAttempt.exam).joinedload(Exam.questions)
    )
    result = await db.execute(query)
    att = result.unique().scalars().first()
    if not att:
        raise HTTPException(status_code=404, detail="Attempt not found")

    is_completed_res = await db.execute(
        select(func.count(ExamAttempt.id)).where(
            ExamAttempt.exam_id == att.exam.id,
            ExamAttempt.user_id == user.id
        )
    )
    is_completed = (is_completed_res.scalar() or 0) > 0

    attempt_count_res = await db.execute(
        select(func.count(ExamAttempt.id)).where(ExamAttempt.exam_id == att.exam.id)
    )
    attempt_count = attempt_count_res.scalar() or 0

    exam_dict = {
        "id": att.exam.id,
        "title": att.exam.title,
        "skill": att.exam.skill,
        "task_type": att.exam.task_type,
        "difficulty": att.exam.difficulty,
        "duration_minutes": att.exam.duration_minutes,
        "topic": att.exam.topic,
        "tags": att.exam.tags,
        "questions": att.exam.questions,
        "is_completed": is_completed,
        "attempt_count": attempt_count
    }

    return ResponseSchema(
        success=True,
        message="Thành công",
        data=ExamAttemptDetailResponseSchema.model_validate({
            "id": att.id,
            "exam_id": att.exam_id,
            "status": att.status,
            "started_at": att.started_at,
            "submitted_at": att.submitted_at,
            "exam": exam_dict
        })
    )

