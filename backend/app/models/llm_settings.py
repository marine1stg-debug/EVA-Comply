"""Single-row platform LLM connector configuration (super-admin only).

Holds the connection to a private/self-hosted or hosted LLM API used for
AI-assisted evidence review and recommendation generation. The API key is
stored server-side only and is NEVER returned to the browser - responses
expose a masked hint (``••••1234``) plus a ``has_key`` flag instead.
"""
import uuid
from sqlalchemy import String, Boolean, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from app.models.base import TimestampMixin


class LlmSettings(Base, TimestampMixin):
    """Single-row global LLM connector config."""
    __tablename__ = "llm_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # openai = OpenAI / OpenAI-compatible (Azure, vLLM, LM Studio, OpenRouter…)
    # anthropic = Anthropic Messages API
    # ollama = local Ollama server
    provider: Mapped[str] = mapped_column(String(20), default="openai")
    base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    model: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Secret - server-side only, never serialized to clients.
    api_key: Mapped[str | None] = mapped_column(Text, nullable=True)

    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30)

    # Optional custom auth header (e.g. some gateways want "x-api-key" or a
    # bespoke header instead of the provider default).
    extra_header_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    extra_header_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Last test-connection result (for the settings page status line).
    last_tested_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_test_ok: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_test_msg: Mapped[str | None] = mapped_column(Text, nullable=True)
