from sqlalchemy import TIMESTAMP, BigInteger, Column, Float, ForeignKey, Table, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from app.db.base import metadata

notes = Table(
    "notes",
    metadata,
    Column(
        "id",
        BigInteger,
        primary_key=True,
        index=True,
        autoincrement=True,
    ),
    Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=True,
    ),
    Column("content", Text, nullable=False),
    Column("embedding", ARRAY(Float), nullable=True),
    Column("created_at", TIMESTAMP(timezone=True)),
    Column("updated_at", TIMESTAMP(timezone=True)),
    schema="public",
)
