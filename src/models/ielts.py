import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text, Boolean, JSON, Table, Column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base
from src.models.auth import utcnow

class Test(Base):
    __tablename__ = "tests"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    skill: Mapped[str] = mapped_column(String(50), nullable=False) # READING, LISTENING, WRITING, SPEAKING
    test_type: Mapped[str] = mapped_column(String(50), nullable=False) # ACADEMIC, GENERAL
    difficulty: Mapped[str] = mapped_column(String(50), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    
    sections = relationship("TestSection", back_populates="test", cascade="all, delete-orphan")


class TestSection(Base):
    __tablename__ = "test_sections"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), nullable=False)
    section_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=True)
    instructions: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    
    test = relationship("Test", back_populates="sections")
    passages = relationship("Passage", back_populates="section", cascade="all, delete-orphan")


class Passage(Base):
    __tablename__ = "passages"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("test_sections.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=True)
    audio_url: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    
    section = relationship("TestSection", back_populates="passages")
    questions = relationship("Question", back_populates="passage", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("test_sections.id", ondelete="CASCADE"), nullable=True)
    passage_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("passages.id", ondelete="CASCADE"), nullable=True)
    question_number: Mapped[int] = mapped_column(Integer, nullable=False)
    question_type: Mapped[str] = mapped_column(String(50), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    correct_answer: Mapped[str] = mapped_column(Text, nullable=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=True)
    points: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    
    passage = relationship("Passage", back_populates="questions")
    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan")


class QuestionOption(Base):
    __tablename__ = "question_options"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    option_key: Mapped[str] = mapped_column(String(10), nullable=False)
    option_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    
    question = relationship("Question", back_populates="options")


class TestAttempt(Base):
    __tablename__ = "test_attempts"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    test_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False) # IN_PROGRESS, SUBMITTED, GRADED
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    score: Mapped[float] = mapped_column(Float, nullable=True)
    band_score: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    
    answers = relationship("TestAttemptAnswer", back_populates="attempt", cascade="all, delete-orphan")


class TestAttemptAnswer(Base):
    __tablename__ = "test_attempt_answers"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("test_attempts.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=True)
    points_earned: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    
    attempt = relationship("TestAttempt", back_populates="answers")


class Topic(Base):
    __tablename__ = "topics"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    
    exams = relationship("Exam", back_populates="topic")


# Association table for Exam and Tag (Many-to-Many)
exam_tags = Table(
    "exam_tags",
    Base.metadata,
    Column("exam_id", UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
)


class Tag(Base):
    __tablename__ = "tags"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)  # JSON string {"vi": "...", "en": "..."}
    skill: Mapped[str] = mapped_column(String(50), nullable=False) # READING, LISTENING, WRITING, SPEAKING
    category: Mapped[str] = mapped_column(String(100), nullable=False) # e.g. READING_Q_TYPE, WRITING_T1_TYPE
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    
    exams = relationship("Exam", secondary="exam_tags", back_populates="tags")


class Exam(Base):
    __tablename__ = "exams"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    exam_type: Mapped[str] = mapped_column(String(50), default="IELTS")
    skill: Mapped[str] = mapped_column(String(50), nullable=False) # LISTENING, READING, WRITING, SPEAKING
    task_type: Mapped[str] = mapped_column(String(50), nullable=False) # TASK_1, TASK_2, FULL_TEST
    topic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False) # EASY, MEDIUM, HARD
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PUBLISHED") # DRAFT, PUBLISHED
    thumbnail_url: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    
    topic = relationship("Topic", back_populates="exams")
    tags = relationship("Tag", secondary="exam_tags", back_populates="exams")
    questions = relationship("ExamQuestion", back_populates="exam", cascade="all, delete-orphan", order_by="ExamQuestion.order_index")
    attempts = relationship("ExamAttempt", back_populates="exam", cascade="all, delete-orphan")


class ExamQuestion(Base):
    __tablename__ = "exam_questions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    parent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("exam_questions.id", ondelete="CASCADE"), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    skill: Mapped[str] = mapped_column(String(50), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    question_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=True)
    instructions: Mapped[str] = mapped_column(Text, nullable=True)
    content = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    question_metadata = mapped_column("metadata", JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    
    exam = relationship("Exam", back_populates="questions")
    children = relationship("ExamQuestion", back_populates="parent", cascade="all, delete-orphan")
    parent = relationship("ExamQuestion", back_populates="children", remote_side=[id])


class ExamAttempt(Base):
    __tablename__ = "exam_attempts"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="IN_PROGRESS") # NOT_STARTED, IN_PROGRESS, SUBMITTED
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    
    exam = relationship("Exam", back_populates="attempts")
    user = relationship("User")


class IeltsQuestion(Base):
    """
    Question Bank - Câu hỏi đơn lẻ có thể làm riêng hoặc gom vào Full Exam.
    skill + part + question_type cho phép filter 3 cấp:
      WRITING → TASK_1 → bar_chart
      SPEAKING → PART_2 → describe_person
    """
    __tablename__ = "ielts_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Kỹ năng: WRITING | SPEAKING
    skill: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # Phần thi: TASK_1 | TASK_2 | PART_1 | PART_2 | PART_3
    part: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # Dạng đề: bar_chart | line_graph | agree_disagree | describe_person | ...
    question_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Nội dung câu hỏi / đề bài
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    # URL ảnh (chủ yếu dùng cho Writing Task 1)
    image_url: Mapped[str] = mapped_column(Text, nullable=True)
    # Các ý cần trình bày (chủ yếu dùng cho Speaking Part 2)
    bullet_points: Mapped[list] = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # Relationships
    exam_links = relationship("IeltsExamQuestion", back_populates="question", cascade="all, delete-orphan")
    attempts = relationship("IeltsAttempt", back_populates="question", foreign_keys="IeltsAttempt.question_id")


class IeltsExam(Base):
    """
    Full Exam - tập hợp nhiều IeltsQuestion theo thứ tự.
    Học viên có thể làm trọn vẹn 1 đề gồm nhiều phần khác nhau.
    """
    __tablename__ = "ielts_exams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    # True = học viên thấy được; False = đang soạn
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Danh sách câu hỏi theo thứ tự
    question_links = relationship(
        "IeltsExamQuestion",
        back_populates="exam",
        cascade="all, delete-orphan",
        order_by="IeltsExamQuestion.order_index"
    )
    attempts = relationship("IeltsAttempt", back_populates="exam", foreign_keys="IeltsAttempt.exam_id")


class IeltsExamQuestion(Base):
    """
    Join table M2M: IeltsExam ↔ IeltsQuestion.
    Lưu thứ tự (order_index) của câu hỏi trong đề.
    """
    __tablename__ = "ielts_exam_questions"

    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ielts_exams.id", ondelete="CASCADE"), primary_key=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ielts_questions.id", ondelete="CASCADE"), primary_key=True
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    exam = relationship("IeltsExam", back_populates="question_links")
    question = relationship("IeltsQuestion", back_populates="exam_links")


class IeltsAttempt(Base):
    """
    Lịch sử làm bài của học viên.
    - question_id NOT NULL, exam_id NULL  → làm câu đơn lẻ
    - question_id NULL,    exam_id NOT NULL → làm full exam
    (CHECK constraint đảm bảo chính xác 1 trong 2)
    """
    __tablename__ = "ielts_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # Exactly one of question_id / exam_id phải có giá trị
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ielts_questions.id", ondelete="CASCADE"), nullable=True
    )
    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ielts_exams.id", ondelete="CASCADE"), nullable=True
    )
    # IN_PROGRESS | SUBMITTED | GRADED
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="IN_PROGRESS")
    # Bài làm text (writing / speaking transcript sau khi AI xử lý)
    answer_text: Mapped[str] = mapped_column(Text, nullable=True)
    # File audio (speaking)
    audio_url: Mapped[str] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user = relationship("User")
    question = relationship("IeltsQuestion", back_populates="attempts", foreign_keys=[question_id])
    exam = relationship("IeltsExam", back_populates="attempts", foreign_keys=[exam_id])

