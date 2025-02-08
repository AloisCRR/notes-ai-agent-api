from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int]
    user_id: Mapped[UUID]
    message: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return (
            f"ChatMessage(id={self.id!r}, chat_id={self.chat_id!r}, "
            f"user_id={self.user_id!r}, message={self.message!r})"
        )
