import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from src.db.base import Base
from src.models.auth import utcnow


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    order_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    plan: Mapped[str] = mapped_column(String(50), default="PREMIUM_1M")
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="VND")
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    payment_provider: Mapped[str] = mapped_column(String(20), nullable=False, default="SEPAY", server_default="SEPAY")
    premium_days: Mapped[int] = mapped_column(Integer, default=30)
    pg_transaction_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    raw_webhook_payload: Mapped[Optional[dict]] = mapped_column(
        JSON().with_variant(JSONB(astext_type=Text()), "postgresql"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
