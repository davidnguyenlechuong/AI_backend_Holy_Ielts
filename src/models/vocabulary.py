import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from src.db.base import Base
from src.models.auth import utcnow

class Vocabulary(Base):
    __tablename__ = "vocabularies"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    word: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    lemma: Mapped[str] = mapped_column(String(255), nullable=True)
    part_of_speech: Mapped[str] = mapped_column(String(50), nullable=True)
    definition: Mapped[str] = mapped_column(Text, nullable=True)
    example_sentence: Mapped[str] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class UserVocabulary(Base):
    __tablename__ = "user_vocabularies"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    vocabulary_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vocabularies.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="LEARNING")
    mastery_level: Mapped[int] = mapped_column(default=0)
    note: Mapped[str] = mapped_column(Text, nullable=True)
    last_reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class SubmissionVocabulary(Base):
    __tablename__ = "submission_vocabularies"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    vocabulary_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vocabularies.id", ondelete="CASCADE"), nullable=False)
    context: Mapped[str] = mapped_column(Text, nullable=True)
    importance: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
