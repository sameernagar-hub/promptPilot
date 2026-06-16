from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


EMBEDDING_DIMENSIONS = 1536


def generate_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    email: Mapped[str | None] = mapped_column(String(320), unique=True, nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    sessions: Mapped[list["ProblemSession"]] = relationship(back_populates="user")
    saved_prompts: Mapped[list["SavedPrompt"]] = relationship(back_populates="user")


class ProblemSession(Base):
    __tablename__ = "problem_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    raw_input: Mapped[str] = mapped_column(Text)
    detected_domain: Mapped[str | None] = mapped_column(String(120), nullable=True)
    detected_intent: Mapped[str | None] = mapped_column(String(120), nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(40), nullable=True)
    classification: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    user_settings: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(60), default="created")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    user: Mapped[User | None] = relationship(back_populates="sessions")
    question_rows: Mapped[list["ClarifyingQuestion"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ClarifyingQuestion.position",
    )
    prompts: Mapped[list["PromptVariant"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="PromptVariant.created_at",
    )
    saved_prompts: Mapped[list["SavedPrompt"]] = relationship(back_populates="session")

    @property
    def clarifying_questions(self) -> list[dict[str, Any]]:
        return [question.to_api_dict() for question in self.question_rows]

    @property
    def answers(self) -> dict[str, str]:
        return {
            question.question_key: question.answer
            for question in self.question_rows
            if question.answer
        }

    @property
    def prompt_variant_ids(self) -> list[str]:
        return [prompt.id for prompt in self.prompts if prompt.is_active]

    def touch(self, status: str | None = None) -> None:
        if status:
            self.status = status
        self.updated_at = utc_now()


class ClarifyingQuestion(Base):
    __tablename__ = "clarifying_questions"
    __table_args__ = (
        Index(
            "ix_clarifying_questions_session_key",
            "session_id",
            "question_key",
            unique=True,
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("problem_sessions.id"), index=True)
    question_key: Mapped[str] = mapped_column(String(120))
    question: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text)
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    session: Mapped[ProblemSession] = relationship(back_populates="question_rows")

    def to_api_dict(self) -> dict[str, Any]:
        return {
            "id": self.question_key,
            "question": self.question,
            "reason": self.reason,
            "required": self.required,
        }


class PromptVariant(Base):
    __tablename__ = "prompt_variants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("problem_sessions.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    strategy: Mapped[str] = mapped_column(String(120))
    prompt_text: Mapped[str] = mapped_column(Text)
    recommendation_label: Mapped[str] = mapped_column(String(80), default="candidate")
    score_total: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_breakdown: Mapped[dict[str, float]] = mapped_column(JSONB, default=dict)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    session: Mapped[ProblemSession] = relationship(back_populates="prompts")
    score_rows: Mapped[list["PromptScore"]] = relationship(
        back_populates="prompt_variant",
        cascade="all, delete-orphan",
        order_by="PromptScore.created_at",
    )
    saved_prompts: Mapped[list["SavedPrompt"]] = relationship(back_populates="prompt")
    embeddings: Mapped[list["PromptEmbedding"]] = relationship(back_populates="prompt_variant")


class PromptScore(Base):
    __tablename__ = "prompt_scores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    prompt_variant_id: Mapped[str] = mapped_column(ForeignKey("prompt_variants.id"), index=True)
    score_total: Mapped[float] = mapped_column(Float)
    score_breakdown: Mapped[dict[str, float]] = mapped_column(JSONB, default=dict)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    scorer_version: Mapped[str] = mapped_column(String(80), default="rule-based-v1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    prompt_variant: Mapped[PromptVariant] = relationship(back_populates="score_rows")


class SavedPrompt(Base):
    __tablename__ = "saved_prompts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    prompt_id: Mapped[str] = mapped_column(ForeignKey("prompt_variants.id"), index=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("problem_sessions.id"), index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(200))
    prompt_text: Mapped[str] = mapped_column(Text)
    strategy: Mapped[str] = mapped_column(String(120))
    label: Mapped[str | None] = mapped_column(String(160), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    prompt: Mapped[PromptVariant] = relationship(back_populates="saved_prompts")
    session: Mapped[ProblemSession] = relationship(back_populates="saved_prompts")
    user: Mapped[User | None] = relationship(back_populates="saved_prompts")


class PromptSource(Base):
    __tablename__ = "prompt_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    source_name: Mapped[str] = mapped_column(String(200))
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    license: Mapped[str | None] = mapped_column(String(200), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text)
    normalized_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    domain: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    intent: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    format: Mapped[str | None] = mapped_column(String(80), nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(40), nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    embeddings: Mapped[list["PromptEmbedding"]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
    )


class PromptEmbedding(Base):
    __tablename__ = "prompt_embeddings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    source_id: Mapped[str | None] = mapped_column(ForeignKey("prompt_sources.id"), nullable=True)
    prompt_variant_id: Mapped[str | None] = mapped_column(
        ForeignKey("prompt_variants.id"),
        nullable=True,
    )
    embedding_model: Mapped[str] = mapped_column(String(160), default="pending")
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIMENSIONS), nullable=True)
    embedding_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    source: Mapped[PromptSource | None] = relationship(back_populates="embeddings")
    prompt_variant: Mapped[PromptVariant | None] = relationship(back_populates="embeddings")


class DomainPack(Base):
    __tablename__ = "domain_packs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    domain: Mapped[str] = mapped_column(String(120), index=True)
    intents: Mapped[list[str]] = mapped_column(JSONB, default=list)
    prompt_strategies: Mapped[list[str]] = mapped_column(JSONB, default=list)
    risk_rules: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
