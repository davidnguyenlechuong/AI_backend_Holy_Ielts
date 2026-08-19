"""
Admin Service — Business logic cho Question Bank & Exam
"""
import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.admin.repository import IeltsQuestionRepository, IeltsExamRepository
from src.modules.admin.schemas import (
    CreateIeltsQuestionRequest,
    UpdateIeltsQuestionRequest,
    IeltsQuestionResponse,
    IeltsQuestionListData,
    CreateIeltsExamRequest,
    UpdateIeltsExamRequest,
    IeltsExamResponse,
    IeltsExamListData,
    IeltsExamQuestionItem,
)


class AdminQuestionService:
    def __init__(self, db: AsyncSession):
        self.repo = IeltsQuestionRepository(db)

    async def get_questions(
        self,
        page: int,
        page_size: int,
        skill: Optional[str],
        part: Optional[str],
        question_type: Optional[str],
    ) -> IeltsQuestionListData:
        items, total = await self.repo.get_list(
            page=page, page_size=page_size,
            skill=skill, part=part, question_type=question_type,
        )
        return IeltsQuestionListData(
            items=[IeltsQuestionResponse.model_validate(q) for q in items],
            total=total, page=page, pageSize=page_size,
        )

    async def create_question(self, body: CreateIeltsQuestionRequest) -> IeltsQuestionResponse:
        q = await self.repo.create(
            skill=body.skill,
            part=body.part,
            question_type=body.questionType,
            topic=body.topic,
            image_url=body.imageUrl,
            bullet_points=body.bulletPoints,
        )
        return IeltsQuestionResponse.model_validate(q)

    async def update_question(
        self, qid: uuid.UUID, body: UpdateIeltsQuestionRequest
    ) -> IeltsQuestionResponse:
        q = await self.repo.get_by_id(qid)
        if not q:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Câu hỏi '{qid}' không tồn tại")
        updated = await self.repo.update(
            q=q,
            skill=body.skill, part=body.part, question_type=body.questionType,
            topic=body.topic, image_url=body.imageUrl, bullet_points=body.bulletPoints,
        )
        return IeltsQuestionResponse.model_validate(updated)

    async def delete_question(self, qid: uuid.UUID) -> None:
        q = await self.repo.get_by_id(qid)
        if not q:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Câu hỏi '{qid}' không tồn tại")
        await self.repo.delete(q)


class AdminExamService:
    def __init__(self, db: AsyncSession):
        self.repo = IeltsExamRepository(db)
        self.q_repo: IeltsQuestionRepository = None  # type: ignore

    def _set_q_repo(self, db: AsyncSession):
        self.q_repo = IeltsQuestionRepository(db)

    def _build_exam_response(self, exam) -> IeltsExamResponse:
        """Convert IeltsExam ORM object → IeltsExamResponse schema"""
        questions_data = []
        for link in (exam.question_links or []):
            q_resp = IeltsQuestionResponse.model_validate(link.question)
            questions_data.append(
                IeltsExamQuestionItem.model_validate({
                    "order_index": link.order_index,
                    "question": q_resp,
                })
            )
        return IeltsExamResponse.model_validate({
            "id": exam.id,
            "title": exam.title,
            "description": exam.description,
            "is_published": exam.is_published,
            "questions": questions_data,
            "created_at": exam.created_at,
            "updated_at": exam.updated_at,
        })

    async def get_exams(
        self, page: int, page_size: int, published_only: bool = False
    ) -> IeltsExamListData:
        items, total = await self.repo.get_list(
            page=page, page_size=page_size, published_only=published_only
        )
        return IeltsExamListData(
            items=[self._build_exam_response(e) for e in items],
            total=total, page=page, pageSize=page_size,
        )

    async def create_exam(
        self, body: CreateIeltsExamRequest, db: AsyncSession
    ) -> IeltsExamResponse:
        # Validate all question IDs exist
        q_repo = IeltsQuestionRepository(db)
        entries = []
        for item in body.questions:
            q = await q_repo.get_by_id(item.questionId)
            if not q:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Câu hỏi '{item.questionId}' không tồn tại"
                )
            entries.append({"question_id": item.questionId, "order_index": item.orderIndex})

        exam = await self.repo.create(
            title=body.title,
            description=body.description,
            is_published=body.isPublished,
            question_entries=entries,
            db_questions=[],
        )
        return self._build_exam_response(exam)

    async def update_exam(
        self, exam_id: uuid.UUID, body: UpdateIeltsExamRequest, db: AsyncSession
    ) -> IeltsExamResponse:
        exam = await self.repo.get_by_id(exam_id)
        if not exam:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Đề '{exam_id}' không tồn tại")

        q_repo = IeltsQuestionRepository(db)
        entries = []
        for item in body.questions:
            q = await q_repo.get_by_id(item.questionId)
            if not q:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Câu hỏi '{item.questionId}' không tồn tại"
                )
            entries.append({"question_id": item.questionId, "order_index": item.orderIndex})

        updated = await self.repo.update(
            exam=exam,
            title=body.title,
            description=body.description,
            is_published=body.isPublished,
            question_entries=entries,
        )
        return self._build_exam_response(updated)

    async def delete_exam(self, exam_id: uuid.UUID) -> None:
        exam = await self.repo.get_by_id(exam_id)
        if not exam:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Đề '{exam_id}' không tồn tại")
        await self.repo.delete(exam)
