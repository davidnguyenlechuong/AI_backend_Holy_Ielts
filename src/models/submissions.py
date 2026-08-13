import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Text, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base
from src.models.auth import utcnow

class Submission(Base):
    __tablename__ = "submissions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill: Mapped[str] = mapped_column(String(50), nullable=False) # WRITING, SPEAKING
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False) # PENDING, PROCESSING, COMPLETED, FAILED
    input_text: Mapped[str] = mapped_column(Text, nullable=True)
    audio_url: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    
    grading_result = relationship("GradingResult", back_populates="submission", uselist=False, cascade="all, delete-orphan")
    speaking_analysis = relationship("SpeakingAnalysis", back_populates="submission", uselist=False, cascade="all, delete-orphan")


class GradingResult(Base):
    __tablename__ = "grading_results"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, unique=True)
    overall_band: Mapped[float] = mapped_column(Float, nullable=True)
    feedback: Mapped[str] = mapped_column(Text, nullable=True)
    model_provider: Mapped[str] = mapped_column(String(50), nullable=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=True)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=True)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    
    submission = relationship("Submission", back_populates="grading_result")
    criteria_scores = relationship("GradingCriteriaScore", back_populates="grading_result", cascade="all, delete-orphan")


class GradingCriteriaScore(Base):
    __tablename__ = "grading_criteria_scores"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    grading_result_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("grading_results.id", ondelete="CASCADE"), nullable=False)
    criterion: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    feedback: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    
    grading_result = relationship("GradingResult", back_populates="criteria_scores")


class SpeakingAnalysis(Base):
    __tablename__ = "speaking_analysis"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, unique=True)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, nullable=True)
    words_per_minute: Mapped[float] = mapped_column(Float, nullable=True)
    pause_count: Mapped[int] = mapped_column(Integer, nullable=True)
    total_pause_seconds: Mapped[float] = mapped_column(Float, nullable=True)
    filler_count: Mapped[int] = mapped_column(Integer, nullable=True)
    filler_words = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    transcript: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    
    submission = relationship("Submission", back_populates="speaking_analysis")
