import uuid
from typing import Optional
from sqlalchemy import String, Text, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.base import TimestampMixin


class Policy(Base, TimestampMixin):
    """A managed policy template.

    Seeded from the built-in policy_library .docx files; Super Admins can add,
    edit metadata, replace the file, toggle availability, and set the category
    (control family) it maps to. The Controls view shows the active policy whose
    keywords match a control's domain.

      source = 'builtin'  -> file served from backend/policy_library/<slug>.docx
      source = 'upload'   -> file served from <STORAGE_LOCAL_PATH>/policies/<slug>.docx
      keywords = comma-separated lowercase tokens; a control matches when its
                 domain contains ALL tokens of a keyword group (groups split by '|').
    """
    __tablename__ = "policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    name_fr: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    category: Mapped[str] = mapped_column(String(120), default="General")        # control family label
    category_fr: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_fr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    keywords: Mapped[str] = mapped_column(String(300), default="")               # e.g. "access,control" or "risk,assessment"
    slug: Mapped[str] = mapped_column(String(200), nullable=False)               # file base name (no extension)
    source: Mapped[str] = mapped_column(String(10), default="builtin")           # builtin | upload
    has_fr: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)               # "Available" toggle
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
