"""
Admin Schemas — Quản lý Question Bank & Full Exam
"""
import uuid
from typing import Optional, List
from datetime import datetime
from pydantic import Field, field_validator, model_validator
from src.shared.base.schema import BaseSchema

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

VALID_SKILLS = {"WRITING", "SPEAKING"}

VALID_PARTS = {"TASK_1", "TASK_2", "PART_1", "PART_2", "PART_3"}

# Mapping skill+part → các dạng đề hợp lệ
VALID_QUESTION_TYPES: dict[str, set[str]] = {
    "WRITING:TASK_1": {
        "bar_chart", "line_graph", "pie_chart", "table",
        "mixed_charts", "process_diagram", "map",
    },
    "WRITING:TASK_2": {
        "agree_disagree", "discuss_both_views", "advantages_disadvantages",
        "advantages_outweigh", "problems_solutions", "causes_solutions",
        "causes_effects", "positive_negative", "two_part_questions",
    },
    "SPEAKING:PART_1": {
        "personal_info", "work_study", "hometown", "home_accommodation",
        "likes_dislikes", "habits_frequency", "preferences",
    },
    "SPEAKING:PART_2": {
        "describe_person", "describe_place", "describe_event", "describe_object",
    },
    "SPEAKING:PART_3": {
        "discussion",
    },
}


def get_valid_types(skill: str, part: str) -> set[str]:
    return VALID_QUESTION_TYPES.get(f"{skill}:{part}", set())


# ─────────────────────────────────────────────────────────────────────────────
# IeltsQuestion Schemas
# ─────────────────────────────────────────────────────────────────────────────

class IeltsQuestionResponse(BaseSchema):
    """Response object khớp với FE — camelCase aliases"""
    id: uuid.UUID
    skill: str
    part: str
    questionType: str = Field(alias="question_type")
    topic: str
    imageUrl: Optional[str] = Field(None, alias="image_url")
    bulletPoints: Optional[List[str]] = Field(None, alias="bullet_points")
    createdAt: str = Field(alias="created_at")

    @field_validator("createdAt", mode="before")
    @classmethod
    def format_created_at(cls, v):
        if isinstance(v, datetime):
            return v.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        return v

    model_config = {"from_attributes": True, "populate_by_name": True}


class IeltsQuestionListData(BaseSchema):
    items: List[IeltsQuestionResponse]
    total: int
    page: int
    pageSize: int


class CreateIeltsQuestionRequest(BaseSchema):
    skill: str
    part: str
    questionType: str                        # camelCase từ FE
    topic: str
    imageUrl: Optional[str] = None
    bulletPoints: Optional[List[str]] = None

    @field_validator("skill")
    @classmethod
    def validate_skill(cls, v: str) -> str:
        v = v.upper()
        if v not in VALID_SKILLS:
            raise ValueError(f"skill phải là: {', '.join(sorted(VALID_SKILLS))}")
        return v

    @field_validator("part")
    @classmethod
    def validate_part(cls, v: str) -> str:
        v = v.upper()
        if v not in VALID_PARTS:
            raise ValueError(f"part phải là: {', '.join(sorted(VALID_PARTS))}")
        return v

    @model_validator(mode="after")
    def validate_question_type(self):
        valid = get_valid_types(self.skill, self.part)
        if valid and self.questionType not in valid:
            raise ValueError(
                f"questionType '{self.questionType}' không hợp lệ cho {self.skill} {self.part}. "
                f"Các dạng hợp lệ: {', '.join(sorted(valid))}"
            )
        return self


class UpdateIeltsQuestionRequest(CreateIeltsQuestionRequest):
    """Giống Create — full override"""
    pass


# ─────────────────────────────────────────────────────────────────────────────
# IeltsExam Schemas
# ─────────────────────────────────────────────────────────────────────────────

class IeltsExamQuestionItem(BaseSchema):
    """Một câu hỏi trong đề + thứ tự của nó"""
    orderIndex: int = Field(alias="order_index")
    question: IeltsQuestionResponse

    model_config = {"from_attributes": True, "populate_by_name": True}


class IeltsExamResponse(BaseSchema):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    isPublished: bool = Field(alias="is_published")
    questions: List[IeltsExamQuestionItem] = Field(default_factory=list)
    createdAt: str = Field(alias="created_at")
    updatedAt: str = Field(alias="updated_at")

    @field_validator("createdAt", "updatedAt", mode="before")
    @classmethod
    def format_dt(cls, v):
        if isinstance(v, datetime):
            return v.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        return v

    model_config = {"from_attributes": True, "populate_by_name": True}


class IeltsExamListData(BaseSchema):
    items: List[IeltsExamResponse]
    total: int
    page: int
    pageSize: int


class ExamQuestionInput(BaseSchema):
    """Một item trong danh sách câu hỏi khi tạo/sửa exam"""
    questionId: uuid.UUID
    orderIndex: int = 1


class CreateIeltsExamRequest(BaseSchema):
    title: str
    description: Optional[str] = None
    isPublished: bool = False
    questions: List[ExamQuestionInput] = Field(default_factory=list)


class UpdateIeltsExamRequest(BaseSchema):
    title: str
    description: Optional[str] = None
    isPublished: bool = False
    questions: List[ExamQuestionInput] = Field(default_factory=list)
