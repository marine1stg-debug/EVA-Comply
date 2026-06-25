import uuid
from sqlalchemy import String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import TimestampMixin


class Backup(Base, TimestampMixin):
    """Metadata for a server-stored backup snapshot. The JSON bundle itself is
    written to a file on disk (filename); this row records what it contains."""
    __tablename__ = "backups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    label: Mapped[str] = mapped_column(String, default="")
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_by_name: Mapped[str] = mapped_column(String, default="")
    categories: Mapped[list] = mapped_column(JSON, default=list)
    client_ids: Mapped[list] = mapped_column(JSON, default=list)
    scope: Mapped[str] = mapped_column(String, default="")        # human-readable scope summary
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    filename: Mapped[str] = mapped_column(String, default="")
