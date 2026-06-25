"""Internal improvement / fix requests raised by the EVA team.

A lightweight issue log: a Super Admin (or a dev/tester super-admin account)
records something to fix or improve, optionally with one or more screenshots
(captured in-app or pasted). Requests are listed, can be copied individually to
paste into Claude, or exported together as a Word document.

This is an internal tool: it is never exposed to client tenants.
"""
import uuid
from typing import Optional

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import TimestampMixin


class ImprovementRequest(Base, TimestampMixin):
    __tablename__ = "improvement_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Author (snapshot of name/role so the log reads well even if the user changes later).
    author_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    author_name: Mapped[str] = mapped_column(String(200), nullable=False)
    author_role: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(30), nullable=False, default="bug")     # bug | idea | question | other
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")  # low | medium | high
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")      # open | in_progress | done | wont_fix
    page_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)          # where in the app it was raised
    resolution_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)          # how it was implemented / closing note

    attachments: Mapped[list["ImprovementAttachment"]] = relationship(
        back_populates="request", cascade="all, delete-orphan", lazy="selectin",
    )


class ImprovementAttachment(Base, TimestampMixin):
    __tablename__ = "improvement_attachments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("improvement_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)        # stored filename on disk
    content_type: Mapped[str] = mapped_column(String(100), nullable=False, default="image/png")
    original_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    request: Mapped["ImprovementRequest"] = relationship(back_populates="attachments")
