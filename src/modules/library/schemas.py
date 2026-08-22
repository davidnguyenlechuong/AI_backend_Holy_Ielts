import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field, field_validator, model_validator
from src.shared.base.schema import BaseSchema


class TagResponseSchema(BaseSchema):
    code: str
    name: Dict[str, str]
    skill: str
    category: str

    @field_validator("name", mode="before")
    @classmethod
    def parse_name(cls, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return {"vi": value, "en": value}
        return value

class ExamQuestionSchema(BaseSchema):
    id: uuid.UUID
    task_type: str
    question_type: str
    content: Optional[dict] = None

class ExamResponseSchema(BaseSchema):
    id: uuid.UUID
    title: Dict[str, str]
    skill: str
    task_type: str
    difficulty: str
    duration_minutes: int
    topic_slug: Optional[str] = None
    tags: List[TagResponseSchema]
    questions: List[ExamQuestionSchema]
    is_completed: bool = False
    attempt_count: int = 0

    @field_validator("title", mode="before")
    @classmethod
    def parse_title(cls, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return {"vi": value, "en": value}
        return value

    @model_validator(mode="before")
    @classmethod
    def extract_topic_slug(cls, data):
        # Extract topic_slug from topic if present
        if not isinstance(data, dict):
            # It is an ORM object
            topic = getattr(data, "topic", None)
            if topic:
                data.topic_slug = getattr(topic, "slug", None)
        else:
            # It is a dictionary
            topic = data.get("topic")
            if topic:
                if isinstance(topic, dict):
                    data["topic_slug"] = topic.get("slug")
                else:
                    data["topic_slug"] = getattr(topic, "slug", None)
        return data

class StartAttemptResponseSchema(BaseSchema):
    attempt_id: uuid.UUID
    exam_id: uuid.UUID
    started_at: str
    status: str


class ExamAttemptResponseSchema(BaseSchema):
    id: uuid.UUID
    examId: uuid.UUID = Field(alias="exam_id")
    status: str
    startedAt: str = Field(alias="started_at")
    submittedAt: Optional[str] = Field(None, alias="submitted_at")

    @field_validator("startedAt", "submittedAt", mode="before")
    @classmethod
    def format_dt(cls, v):
        if isinstance(v, datetime):
            return v.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        return v

    model_config = {"from_attributes": True, "populate_by_name": True}


class ExamAttemptDetailResponseSchema(ExamAttemptResponseSchema):
    exam: Optional[ExamResponseSchema] = None

