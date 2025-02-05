from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Note(Base):
    __tablename__ = "notes"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[UUID]]
    content: Mapped[str]
    embedding: Mapped[Optional[Vector]] = mapped_column(Vector)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return (
            f"Note(id={self.id!r}, user_id={self.user_id!r}, content={self.content!r})"
        )
