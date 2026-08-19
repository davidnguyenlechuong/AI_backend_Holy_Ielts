"""add_ielts_question_bank_tables

Revision ID: a1b2c3d4e5f7
Revises: f1b2c3d4e5f6
Create Date: 2026-08-22 11:42:00.000000

Creates the full IELTS Question Bank schema:
  - ielts_questions  : atomic question units (skill + part + question_type)
  - ielts_exams      : full exam containers
  - ielts_exam_questions : M2M join with order_index
  - ielts_attempts   : student attempt history
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, Sequence[str], None] = 'f1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. ielts_questions — Question Bank (atomic unit)
    op.create_table(
        'ielts_questions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('skill', sa.String(length=20), nullable=False),
        sa.Column('part', sa.String(length=20), nullable=False),
        sa.Column('question_type', sa.String(length=50), nullable=False),
        sa.Column('topic', sa.Text(), nullable=False),
        sa.Column('image_url', sa.Text(), nullable=True),
        sa.Column(
            'bullet_points',
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), 'sqlite'),
            nullable=True
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ielts_questions_skill', 'ielts_questions', ['skill'])
    op.create_index('ix_ielts_questions_part', 'ielts_questions', ['part'])
    op.create_index('ix_ielts_questions_question_type', 'ielts_questions', ['question_type'])

    # 2. ielts_exams — Full Exam containers
    op.create_table(
        'ielts_exams',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. ielts_exam_questions — M2M join with order_index
    op.create_table(
        'ielts_exam_questions',
        sa.Column('exam_id', sa.UUID(), nullable=False),
        sa.Column('question_id', sa.UUID(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['exam_id'], ['ielts_exams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['ielts_questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('exam_id', 'question_id')
    )

    # 4. ielts_attempts — Student attempt history
    op.create_table(
        'ielts_attempts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('question_id', sa.UUID(), nullable=True),
        sa.Column('exam_id', sa.UUID(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='IN_PROGRESS'),
        sa.Column('answer_text', sa.Text(), nullable=True),
        sa.Column('audio_url', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['ielts_questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['exam_id'], ['ielts_exams.id'], ondelete='CASCADE'),
        # XOR: exactly one of question_id / exam_id must be set
        sa.CheckConstraint(
            '(question_id IS NOT NULL AND exam_id IS NULL) OR (question_id IS NULL AND exam_id IS NOT NULL)',
            name='ck_ielts_attempts_question_xor_exam'
        ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('ielts_attempts')
    op.drop_table('ielts_exam_questions')
    op.drop_table('ielts_exams')
    op.drop_index('ix_ielts_questions_question_type', table_name='ielts_questions')
    op.drop_index('ix_ielts_questions_part', table_name='ielts_questions')
    op.drop_index('ix_ielts_questions_skill', table_name='ielts_questions')
    op.drop_table('ielts_questions')
