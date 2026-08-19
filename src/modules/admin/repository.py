"""
Admin Repository — Data access layer cho Question Bank & Exam
"""
import uuid
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload

from src.models.ielts import IeltsQuestion, IeltsExam, IeltsExamQuestion


class IeltsQuestionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_list(
        self,
        page: int = 1,
        page_size: int = 10,
        skill: Optional[str] = None,
        part: Optional[str] = None,
        question_type: Optional[str] = None,
    ) -> Tuple[List[IeltsQuestion], int]:
        query = select(IeltsQuestion)
        if skill:
            query = query.where(IeltsQuestion.skill == skill.upper())
        if part:
            query = query.where(IeltsQuestion.part == part.upper())
        if question_type:
            query = query.where(IeltsQuestion.question_type == question_type)
        query = query.order_by(IeltsQuestion.created_at.desc())

        count_result = await self.db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar_one()

        paginated = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(paginated)
        return list(result.scalars().all()), total

    async def get_by_id(self, qid: uuid.UUID) -> Optional[IeltsQuestion]:
        result = await self.db.execute(
            select(IeltsQuestion).where(IeltsQuestion.id == qid)
        )
        return result.scalars().first()

    async def create(
        self,
        skill: str,
        part: str,
        question_type: str,
        topic: str,
        image_url: Optional[str],
        bullet_points: Optional[List[str]],
    ) -> IeltsQuestion:
        q = IeltsQuestion(
            skill=skill,
            part=part,
            question_type=question_type,
            topic=topic,
            image_url=image_url,
            bullet_points=bullet_points,
        )
        self.db.add(q)
        await self.db.commit()
        await self.db.refresh(q)
        return q

    async def update(
        self,
        q: IeltsQuestion,
        skill: str,
        part: str,
        question_type: str,
        topic: str,
        image_url: Optional[str],
        bullet_points: Optional[List[str]],
    ) -> IeltsQuestion:
        q.skill = skill
        q.part = part
        q.question_type = question_type
        q.topic = topic
        setattr(q, "image_url", image_url)
        setattr(q, "bullet_points", bullet_points)
        await self.db.commit()
        await self.db.refresh(q)
        return q

    async def delete(self, q: IeltsQuestion) -> None:
        await self.db.delete(q)
        await self.db.commit()


class IeltsExamRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_list(
        self,
        page: int = 1,
        page_size: int = 10,
        published_only: bool = False,
    ) -> Tuple[List[IeltsExam], int]:
        query = select(IeltsExam)
        if published_only:
            query = query.where(IeltsExam.is_published.is_(True))
        query = query.order_by(IeltsExam.created_at.desc())

        count_result = await self.db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar_one()

        paginated = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(paginated)
        exams = list(result.scalars().all())

        # Load question links for each exam
        for exam in exams:
            await self.db.refresh(exam, ["question_links"])
        return exams, total

    async def get_by_id(self, exam_id: uuid.UUID) -> Optional[IeltsExam]:
        result = await self.db.execute(
            select(IeltsExam)
            .where(IeltsExam.id == exam_id)
            .options(
                selectinload(IeltsExam.question_links).selectinload(IeltsExamQuestion.question)
            )
        )
        return result.scalars().first()

    async def create(
        self,
        title: str,
        description: Optional[str],
        is_published: bool,
        question_entries: List[dict],  # [{"question_id": UUID, "order_index": int}]
        db_questions: List[IeltsQuestion],
    ) -> IeltsExam:
        exam = IeltsExam(
            title=title,
            description=description,
            is_published=is_published,
        )
        self.db.add(exam)
        await self.db.flush()  # get exam.id

        # Create join records
        for entry in question_entries:
            link = IeltsExamQuestion(
                exam_id=exam.id,
                question_id=entry["question_id"],
                order_index=entry["order_index"],
            )
            self.db.add(link)

        await self.db.commit()
        await self.db.refresh(exam)
        return await self.get_by_id(exam.id)  # type: ignore

    async def update(
        self,
        exam: IeltsExam,
        title: str,
        description: Optional[str],
        is_published: bool,
        question_entries: List[dict],
    ) -> IeltsExam:
        exam.title = title
        setattr(exam, "description", description)
        exam.is_published = is_published

        # Replace all question links
        await self.db.execute(
            delete(IeltsExamQuestion).where(IeltsExamQuestion.exam_id == exam.id)
        )
        for entry in question_entries:
            link = IeltsExamQuestion(
                exam_id=exam.id,
                question_id=entry["question_id"],
                order_index=entry["order_index"],
            )
            self.db.add(link)

        await self.db.commit()
        return await self.get_by_id(exam.id)  # type: ignore

    async def delete(self, exam: IeltsExam) -> None:
        await self.db.delete(exam)
        await self.db.commit()
