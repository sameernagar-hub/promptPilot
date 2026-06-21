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
    prompt_profile: Mapped["UserPromptProfile | None"] = relationship(
        back_populates="user",
        uselist=False,
    )


class UserPromptProfile(Base):
    __tablename__ = "user_prompt_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    profile_key: Mapped[str] = mapped_column(String(80), unique=True, default="local")
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    display_name: Mapped[str] = mapped_column(String(160), default="Local profile")
    status: Mapped[str] = mapped_column(String(40), default="empty")
    summary: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    total_sessions: Mapped[int] = mapped_column(Integer, default=0)
    total_imports: Mapped[int] = mapped_column(Integer, default=0)
    observation_count: Mapped[int] = mapped_column(Integer, default=0)
    last_refreshed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    user: Mapped[User | None] = relationship(back_populates="prompt_profile")
    observations: Mapped[list["TraitObservation"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="TraitObservation.trait_key",
    )
    signals: Mapped[list["PromptingTraitSignal"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="PromptingTraitSignal.created_at",
    )
    imports: Mapped[list["ConversationImport"]] = relationship(back_populates="profile")
    platform_preferences: Mapped[list["PlatformPreference"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    observation_overrides: Mapped[list["ProfileObservationOverride"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    integration_connections: Mapped[list["IntegrationConnection"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
    )


class PromptingTrait(Base):
    __tablename__ = "prompting_traits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    trait_key: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(80), default="foundation")
    scoring_direction: Mapped[str] = mapped_column(String(80), default="higher_is_stronger")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    observations: Mapped[list["TraitObservation"]] = relationship(
        back_populates="trait",
        cascade="all, delete-orphan",
    )
    signals: Mapped[list["PromptingTraitSignal"]] = relationship(
        back_populates="trait",
        cascade="all, delete-orphan",
    )


class TraitObservation(Base):
    __tablename__ = "trait_observations"
    __table_args__ = (
        Index(
            "ix_trait_observations_profile_trait_source",
            "profile_id",
            "trait_key",
            "source_type",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    profile_id: Mapped[str] = mapped_column(ForeignKey("user_prompt_profiles.id"), index=True)
    trait_id: Mapped[str | None] = mapped_column(ForeignKey("prompting_traits.id"), nullable=True)
    trait_key: Mapped[str] = mapped_column(String(120), index=True)
    score: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    summary: Mapped[str] = mapped_column(Text)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    source_type: Mapped[str] = mapped_column(String(80), default="session_summary_v1")
    source_ref: Mapped[str | None] = mapped_column(String(160), nullable=True)
    session_id: Mapped[str | None] = mapped_column(
        ForeignKey("problem_sessions.id"),
        nullable=True,
    )
    prompt_variant_id: Mapped[str | None] = mapped_column(
        ForeignKey("prompt_variants.id"),
        nullable=True,
    )
    imported_message_id: Mapped[str | None] = mapped_column(
        ForeignKey("imported_messages.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    profile: Mapped[UserPromptProfile] = relationship(back_populates="observations")
    trait: Mapped[PromptingTrait | None] = relationship(back_populates="observations")


class ProfileObservationOverride(Base):
    __tablename__ = "profile_observation_overrides"
    __table_args__ = (
        Index(
            "ix_profile_observation_overrides_profile_trait",
            "profile_id",
            "trait_key",
            unique=True,
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    profile_id: Mapped[str] = mapped_column(ForeignKey("user_prompt_profiles.id"), index=True)
    trait_key: Mapped[str] = mapped_column(String(120), index=True)
    action: Mapped[str] = mapped_column(String(40), default="corrected")
    corrected_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    profile: Mapped[UserPromptProfile] = relationship(back_populates="observation_overrides")


class PromptingTraitSignal(Base):
    __tablename__ = "prompting_trait_signals"
    __table_args__ = (
        Index(
            "ix_prompting_trait_signals_profile_trait_source",
            "profile_id",
            "trait_key",
            "source_type",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    profile_id: Mapped[str] = mapped_column(ForeignKey("user_prompt_profiles.id"), index=True)
    trait_id: Mapped[str | None] = mapped_column(ForeignKey("prompting_traits.id"), nullable=True)
    trait_key: Mapped[str] = mapped_column(String(120), index=True)
    signal_key: Mapped[str] = mapped_column(String(160))
    signal_label: Mapped[str] = mapped_column(String(200))
    score: Mapped[float] = mapped_column(Float)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    confidence: Mapped[float] = mapped_column(Float)
    explanation: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    source_type: Mapped[str] = mapped_column(String(80), default="trait_detector_v1")
    source_ref: Mapped[str | None] = mapped_column(String(160), nullable=True)
    session_id: Mapped[str | None] = mapped_column(
        ForeignKey("problem_sessions.id"),
        nullable=True,
    )
    imported_message_id: Mapped[str | None] = mapped_column(
        ForeignKey("imported_messages.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    profile: Mapped[UserPromptProfile] = relationship(back_populates="signals")
    trait: Mapped[PromptingTrait | None] = relationship(back_populates="signals")


class ProblemSession(Base):
    __tablename__ = "problem_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    primary_ai_platform: Mapped[str | None] = mapped_column(String(80), nullable=True)
    rules_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    session_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
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
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

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
            if question.answer and question.answer_state == "answered"
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
    answer_state: Mapped[str] = mapped_column(String(40), default="unanswered")
    revision_count: Mapped[int] = mapped_column(Integer, default=0)
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
            "answer": self.answer,
            "state": self.answer_state,
            "revision_count": self.revision_count,
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
    score_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
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

    @property
    def platform_fit_rating(self) -> float | None:
        value = (self.score_metadata or {}).get("platform_fit_rating")
        return float(value) if value is not None else None

    @property
    def platform_fit_breakdown(self) -> dict[str, float]:
        return dict((self.score_metadata or {}).get("platform_fit_breakdown") or {})

    @property
    def recommendation_summary(self) -> str | None:
        value = (self.score_metadata or {}).get("recommendation_summary")
        return str(value) if value is not None else None

    @property
    def why_this_variant(self) -> str | None:
        value = (self.score_metadata or {}).get("why_this_variant")
        return str(value) if value is not None else None

    @property
    def assumption_notes(self) -> list[str]:
        return list((self.score_metadata or {}).get("assumption_notes") or [])

    @property
    def modification_audit_trail(self) -> list[dict[str, Any]]:
        return list((self.score_metadata or {}).get("modification_audit_trail") or [])

    @property
    def rules_matched(self) -> list[dict[str, Any]]:
        return list((self.score_metadata or {}).get("rules_matched") or [])

    @property
    def user_trait_alignment(self) -> list[dict[str, Any]]:
        return list((self.score_metadata or {}).get("user_trait_alignment") or [])

    @property
    def optimization_paths(self) -> list[dict[str, Any]]:
        return list((self.score_metadata or {}).get("optimization_paths") or [])

    @property
    def recommended_actions(self) -> list[dict[str, Any]]:
        return list((self.score_metadata or {}).get("recommended_actions") or [])

    @property
    def scorer_metadata(self) -> dict[str, Any]:
        return dict((self.score_metadata or {}).get("scorer_metadata") or {})


class PromptScore(Base):
    __tablename__ = "prompt_scores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    prompt_variant_id: Mapped[str] = mapped_column(ForeignKey("prompt_variants.id"), index=True)
    score_total: Mapped[float] = mapped_column(Float)
    score_breakdown: Mapped[dict[str, float]] = mapped_column(JSONB, default=dict)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    scorer_version: Mapped[str] = mapped_column(String(80), default="rule-based-v1")
    scorer_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    prompt_variant: Mapped[PromptVariant] = relationship(back_populates="score_rows")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_session_event", "session_id", "event_type"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    session_id: Mapped[str | None] = mapped_column(
        ForeignKey("problem_sessions.id"),
        nullable=True,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(80), index=True)
    entity_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(120), index=True)
    event_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


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


class ConversationImport(Base):
    __tablename__ = "conversation_imports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    profile_id: Mapped[str] = mapped_column(ForeignKey("user_prompt_profiles.id"), index=True)
    platform: Mapped[str] = mapped_column(String(80), default="manual")
    source_type: Mapped[str] = mapped_column(String(80), default="manual")
    title: Mapped[str | None] = mapped_column(String(240), nullable=True)
    consent_status: Mapped[str] = mapped_column(String(60), default="user_provided")
    redaction_status: Mapped[str] = mapped_column(String(60), default="pending")
    import_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    profile: Mapped[UserPromptProfile] = relationship(back_populates="imports")
    conversations: Mapped[list["ImportedConversation"]] = relationship(
        back_populates="conversation_import",
        cascade="all, delete-orphan",
        order_by="ImportedConversation.created_at",
    )


class ImportedConversation(Base):
    __tablename__ = "imported_conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    import_id: Mapped[str] = mapped_column(ForeignKey("conversation_imports.id"), index=True)
    platform: Mapped[str] = mapped_column(String(80), default="manual")
    external_conversation_id: Mapped[str | None] = mapped_column(String(240), nullable=True)
    title: Mapped[str | None] = mapped_column(String(240), nullable=True)
    conversation_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    conversation_import: Mapped[ConversationImport] = relationship(back_populates="conversations")
    messages: Mapped[list["ImportedMessage"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ImportedMessage.position",
    )


class ImportedMessage(Base):
    __tablename__ = "imported_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("imported_conversations.id"),
        index=True,
    )
    role: Mapped[str] = mapped_column(String(80))
    message_text: Mapped[str] = mapped_column(Text)
    redacted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    message_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    message_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    conversation: Mapped[ImportedConversation] = relationship(back_populates="messages")


class PromptRevision(Base):
    __tablename__ = "prompt_revisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    session_id: Mapped[str | None] = mapped_column(ForeignKey("problem_sessions.id"), nullable=True)
    prompt_variant_id: Mapped[str | None] = mapped_column(
        ForeignKey("prompt_variants.id"),
        nullable=True,
    )
    profile_id: Mapped[str | None] = mapped_column(
        ForeignKey("user_prompt_profiles.id"),
        nullable=True,
    )
    revision_type: Mapped[str] = mapped_column(String(80), default="refinement")
    before_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_text: Mapped[str] = mapped_column(Text)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    revision_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class DomainConfirmation(Base):
    __tablename__ = "domain_confirmations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("problem_sessions.id"), index=True)
    profile_id: Mapped[str | None] = mapped_column(
        ForeignKey("user_prompt_profiles.id"),
        nullable=True,
    )
    detected_domain: Mapped[str | None] = mapped_column(String(160), nullable=True)
    confirmed_domain: Mapped[str | None] = mapped_column(String(160), nullable=True)
    domain_source: Mapped[str] = mapped_column(String(80), default="detected")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class PlatformPreference(Base):
    __tablename__ = "platform_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    profile_id: Mapped[str] = mapped_column(ForeignKey("user_prompt_profiles.id"), index=True)
    platform: Mapped[str] = mapped_column(String(80))
    preference: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    profile: Mapped[UserPromptProfile] = relationship(back_populates="platform_preferences")


class IntegrationConnection(Base):
    __tablename__ = "integration_connections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    profile_id: Mapped[str] = mapped_column(ForeignKey("user_prompt_profiles.id"), index=True)
    platform: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(60), default="planned")
    scopes: Mapped[list[str]] = mapped_column(JSONB, default=list)
    connection_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )

    profile: Mapped[UserPromptProfile] = relationship(back_populates="integration_connections")


class PromptSource(Base):
    __tablename__ = "prompt_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    source_name: Mapped[str] = mapped_column(String(200))
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    license: Mapped[str | None] = mapped_column(String(200), nullable=True)
    allowed_usage: Mapped[str] = mapped_column(
        String(120),
        default="pattern_synthesis_only",
    )
    raw_text: Mapped[str] = mapped_column(Text)
    normalized_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    domain: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    intent: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    prompt_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
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
