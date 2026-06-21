from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


PromptLength = Literal["short", "medium", "deep"]
SkillLevel = Literal["beginner", "practical", "expert"]
Tone = Literal["direct", "friendly", "technical"]
PromptFormat = Literal["checklist", "guide", "table", "conversation", "plan"]
RiskPreference = Literal["safe_only", "normal", "advanced"]
SourcePreference = Literal["none", "web", "official_docs"]
RefinementMode = Literal["refinement", "quick"]
ClarifyingQuestionState = Literal["unanswered", "answered", "skipped"]
TargetPlatform = Literal[
    "codex",
    "claude",
    "chatgpt",
    "gemini",
    "cursor",
    "grok",
    "perplexity",
    "copilot",
    "generic",
    "other",
]
SessionAiPlatform = Literal[
    "chatgpt",
    "claude",
    "grok",
    "perplexity",
    "gemini",
    "copilot",
    "cursor",
    "codex",
    "other",
]
DetailLevel = Literal["concise", "balanced", "exhaustive"]
Formality = Literal["casual", "neutral", "formal"]
TemperaturePreference = Literal["precise", "balanced", "creative"]
ReasoningStyle = Literal["direct_answer", "step_by_step", "ask_first", "explore_options"]
SourceStrictness = Literal["none", "cite_when_needed", "official_only", "evidence_first"]
InteractionMode = Literal["one_shot", "iterative", "agentic"]
PromptSourceAllowedUsage = Literal[
    "pattern_synthesis_only",
    "internal_project_example",
    "licensed_reference",
]
ImportPlatform = Literal[
    "manual",
    "codex",
    "claude",
    "chatgpt",
    "gemini",
    "cursor",
    "windsurf",
    "generic",
]
ImportSourceType = Literal["paste", "markdown", "json", "text", "manual"]


class PromptSettings(BaseModel):
    length: PromptLength = "medium"
    skill_level: SkillLevel = "practical"
    tone: Tone = "friendly"
    format: PromptFormat = "guide"
    risk: RiskPreference = "normal"
    sources: SourcePreference = "none"
    target_platform: TargetPlatform = "generic"
    detail_level: DetailLevel = "balanced"
    formality: Formality = "neutral"
    temperature: TemperaturePreference = "balanced"
    reasoning_style: ReasoningStyle = "ask_first"
    source_strictness: SourceStrictness = "none"
    interaction_mode: InteractionMode = "iterative"


class PromptKnowledgeSourceCreate(BaseModel):
    source_name: str = Field(..., min_length=1, max_length=200)
    source_url: str | None = Field(default=None, max_length=2000)
    author: str | None = Field(default=None, max_length=200)
    license: str = Field(..., min_length=1, max_length=200)
    allowed_usage: PromptSourceAllowedUsage = "pattern_synthesis_only"
    raw_text: str = Field(..., min_length=20, max_length=50_000)
    normalized_text: str | None = Field(default=None, max_length=50_000)
    domain: str | None = Field(default=None, max_length=120)
    intent: str | None = Field(default=None, max_length=120)
    prompt_type: str | None = Field(default=None, max_length=120)
    format: str | None = Field(default=None, max_length=80)
    risk_level: str | None = Field(default=None, max_length=40)
    quality_score: float | None = Field(default=None, ge=0.0, le=1.0)
    source_metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def normalize_required_source_metadata(self) -> "PromptKnowledgeSourceCreate":
        self.source_name = self.source_name.strip()
        self.license = self.license.strip()
        self.raw_text = self.raw_text.strip()
        if not self.source_name:
            raise ValueError("source_name is required")
        if not self.license:
            raise ValueError("license is required")
        return self


class PromptKnowledgeSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_name: str
    source_url: str | None = None
    author: str | None = None
    license: str
    allowed_usage: str
    domain: str | None = None
    intent: str | None = None
    prompt_type: str | None = None
    format: str | None = None
    risk_level: str | None = None
    quality_score: float | None = None
    source_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class RetrievedKnowledgePattern(BaseModel):
    source_id: str
    source_name: str
    source_url: str | None = None
    author: str | None = None
    license: str
    allowed_usage: str
    domain: str | None = None
    intent: str | None = None
    prompt_type: str | None = None
    quality_score: float | None = None
    synthesized_guidance: str
    guardrail_notes: list[str] = Field(default_factory=list)


class KnowledgeRetrievalContext(BaseModel):
    patterns: list[RetrievedKnowledgePattern] = Field(default_factory=list)
    retrieval_metadata: dict[str, Any] = Field(default_factory=dict)


class CreateSessionRequest(BaseModel):
    raw_input: str = Field(..., min_length=3)
    settings: PromptSettings = Field(default_factory=PromptSettings)
    display_name: str = Field(..., min_length=1, max_length=120)
    primary_ai_platform: SessionAiPlatform
    rules_accepted: bool
    session_metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_rules_acceptance(self) -> "CreateSessionRequest":
        self.display_name = self.display_name.strip()
        if not self.display_name:
            raise ValueError("Display name is required")
        if not self.rules_accepted:
            raise ValueError("Rules must be accepted before starting a session")
        return self


class ClassificationResponse(BaseModel):
    domain: str
    primary_domain: str | None = None
    subdomain: str | None = None
    intent: str
    risk_level: str
    confidence: float
    signals: list[str] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    alternative_domains: list[str] = Field(default_factory=list)
    needs_domain_confirmation: bool = False
    confirmed_domain: str | None = None
    domain_source: Literal["detected", "user_confirmed", "user_corrected"] = "detected"


class DomainConfirmationRequest(BaseModel):
    confirmed_domain: str = Field(..., min_length=2, max_length=160)
    accepted: bool = True


class DomainConfirmationResponse(BaseModel):
    session_id: str
    classification: ClassificationResponse


class ClarifyingQuestion(BaseModel):
    id: str
    question: str
    reason: str
    required: bool = True
    answer: str | None = None
    state: ClarifyingQuestionState = "unanswered"
    revision_count: int = 0


class ClarifyingQuestionsResponse(BaseModel):
    session_id: str
    questions: list[ClarifyingQuestion]


class AnswerItem(BaseModel):
    question_id: str
    answer: str | None = Field(default=None, max_length=5000)
    state: ClarifyingQuestionState | None = None

    @model_validator(mode="after")
    def normalize_state(self) -> "AnswerItem":
        if self.answer is not None:
            self.answer = self.answer.strip()
        if self.state is None:
            self.state = "answered" if self.answer else "unanswered"
        if self.state == "answered" and not self.answer:
            raise ValueError("Answered questions require answer text")
        if self.state == "skipped":
            self.answer = None
        return self


class SubmitAnswersRequest(BaseModel):
    answers: list[AnswerItem]


class PromptVariantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    title: str
    strategy: str
    prompt_text: str
    recommendation_label: str
    score_total: float | None = None
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    explanation: str | None = None
    platform_fit_rating: float | None = None
    platform_fit_breakdown: dict[str, float] = Field(default_factory=dict)
    recommendation_summary: str | None = None
    why_this_variant: str | None = None
    assumption_notes: list[str] = Field(default_factory=list)
    modification_audit_trail: list[dict[str, Any]] = Field(default_factory=list)
    rules_matched: list[dict[str, Any]] = Field(default_factory=list)
    user_trait_alignment: list[dict[str, Any]] = Field(default_factory=list)
    optimization_paths: list[dict[str, Any]] = Field(default_factory=list)
    recommended_actions: list[dict[str, Any]] = Field(default_factory=list)
    scorer_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class GeneratePromptsRequest(BaseModel):
    settings: PromptSettings | None = None


class ScorePromptsResponse(BaseModel):
    session_id: str
    prompts: list[PromptVariantResponse]
    recommended_prompt_id: str | None


class PromptEngineRunRequest(BaseModel):
    settings: PromptSettings | None = None
    answers: list[AnswerItem] = Field(default_factory=list)
    mode: RefinementMode = "refinement"


class PromptRevisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str | None
    prompt_variant_id: str | None
    revision_type: str
    before_text: str | None = None
    after_text: str
    rationale: str | None = None
    revision_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class PromptEngineRunResponse(BaseModel):
    session_id: str
    mode: RefinementMode
    classification: ClassificationResponse
    needs_clarification: bool
    questions: list[ClarifyingQuestion]
    prompts: list[PromptVariantResponse]
    recommended_prompt_id: str | None
    assumptions: list[str] = Field(default_factory=list)
    revisions: list[PromptRevisionResponse] = Field(default_factory=list)
    timeline: list[str]
    stage_timings_ms: dict[str, float] = Field(default_factory=dict)
    guardrail_status: Literal["passed", "blocked"] = "passed"
    guardrail_message: str | None = None
    safe_redirect: str | None = None


class RunPromptRequest(BaseModel):
    prompt_id: str | None = None


class RunPromptResponse(BaseModel):
    prompt_id: str
    provider: str
    model: str
    output: str


class SavePromptRequest(BaseModel):
    label: str | None = None


class SavedPromptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    prompt_id: str
    session_id: str
    title: str
    prompt_text: str
    strategy: str
    label: str | None = None
    created_at: datetime


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    display_name: str | None = None
    primary_ai_platform: str | None = None
    rules_accepted: bool = False
    session_metadata: dict[str, Any] = Field(default_factory=dict)
    raw_input: str
    classification: ClassificationResponse | None = None
    detected_domain: str | None
    detected_intent: str | None
    risk_level: str | None
    user_settings: dict
    status: str
    clarifying_questions: list[dict] = Field(default_factory=list)
    answers: dict[str, str] = Field(default_factory=dict)
    prompt_variant_ids: list[str] = Field(default_factory=list)
    prompts: list[PromptVariantResponse] = Field(default_factory=list)
    recommended_prompt_id: str | None = None
    revisions: list[PromptRevisionResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    ended_at: datetime | None = None


class EndSessionResponse(BaseModel):
    id: str
    status: str
    ended_at: datetime


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str | None = None
    entity_type: str
    entity_id: str | None = None
    event_type: str
    event_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class SessionExportResponse(BaseModel):
    session_id: str
    format: Literal["markdown", "json"]
    filename: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeleteSessionDataResponse(BaseModel):
    session_id: str
    deleted: bool
    deleted_counts: dict[str, int] = Field(default_factory=dict)


class ProfileExportResponse(BaseModel):
    format: Literal["markdown", "json"]
    filename: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeleteProfileDataResponse(BaseModel):
    deleted: bool
    deleted_counts: dict[str, int] = Field(default_factory=dict)


class PromptingTraitSignalResponse(BaseModel):
    id: str
    trait_key: str
    signal_key: str
    signal_label: str
    score: float
    weight: float
    confidence: float
    explanation: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    source_type: str
    source_ref: str | None = None
    created_at: datetime


class TraitObservationResponse(BaseModel):
    id: str
    trait_key: str
    trait_label: str
    category: str
    score: float
    confidence: float
    evidence_level: str
    signal_count: int
    summary: str
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    signals: list[PromptingTraitSignalResponse] = Field(default_factory=list)
    source_type: str
    source_ref: str | None = None
    user_corrected: bool = False
    user_note: str | None = None
    created_at: datetime
    updated_at: datetime


class ProfileEvidenceReference(BaseModel):
    type: str
    label: str
    excerpt: str | None = None
    session_id: str | None = None
    imported_message_id: str | None = None
    trait_key: str | None = None
    confidence: float | None = None


class ProfileInsightItem(BaseModel):
    title: str
    detail: str
    confidence: float = 0.0
    evidence: list[ProfileEvidenceReference] = Field(default_factory=list)
    action: str | None = None


class ProfileInsightsResponse(BaseModel):
    profile_status: str
    headline: str
    common_missing_details: list[ProfileInsightItem] = Field(default_factory=list)
    preferences: list[ProfileInsightItem] = Field(default_factory=list)
    frequent_domains: list[ProfileInsightItem] = Field(default_factory=list)
    platform_advice: list[ProfileInsightItem] = Field(default_factory=list)
    recent_revisions: list[ProfileInsightItem] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    empty_state: str | None = None


class ProfileQuestionRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)


class ProfileQuestionResponse(BaseModel):
    question: str
    answer: str
    confidence: float = 0.0
    evidence_level: str
    evidence: list[ProfileEvidenceReference] = Field(default_factory=list)
    suggested_followups: list[str] = Field(default_factory=list)
    needs_more_evidence: bool = False


class ProfileObservationUpdateRequest(BaseModel):
    summary: str | None = Field(default=None, min_length=3, max_length=1200)
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    note: str | None = Field(default=None, max_length=1200)


class ProfileObservationDeleteResponse(BaseModel):
    id: str
    deleted: bool
    trait_key: str


class PlatformPreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    platform: str
    preference: dict[str, Any] = Field(default_factory=dict)
    confidence: float
    created_at: datetime
    updated_at: datetime


class PromptProfileResponse(BaseModel):
    id: str
    profile_key: str
    display_name: str
    status: str
    summary: dict[str, Any] = Field(default_factory=dict)
    total_sessions: int
    total_imports: int
    observation_count: int
    last_refreshed_at: datetime | None = None
    traits: list[TraitObservationResponse] = Field(default_factory=list)
    platform_preferences: list[PlatformPreferenceResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ConversationImportRequest(BaseModel):
    platform: ImportPlatform = "manual"
    source_type: ImportSourceType = "paste"
    title: str | None = Field(default=None, max_length=240)
    raw_text: str = Field(..., min_length=1, max_length=250_000)


class ImportedMessageResponse(BaseModel):
    id: str
    role: str
    text: str
    redacted: bool
    position: int
    message_timestamp: datetime | None = None
    created_at: datetime


class ImportedConversationResponse(BaseModel):
    id: str
    import_id: str
    platform: str
    external_conversation_id: str | None = None
    title: str | None = None
    message_count: int
    messages: list[ImportedMessageResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ConversationImportResponse(BaseModel):
    id: str
    profile_id: str
    platform: str
    source_type: str
    title: str | None = None
    consent_status: str
    redaction_status: str
    conversation_count: int
    message_count: int
    import_metadata: dict[str, Any] = Field(default_factory=dict)
    conversations: list[ImportedConversationResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ConversationImportDeleteResponse(BaseModel):
    id: str
    deleted: bool


class HealthResponse(BaseModel):
    service: str
    status: str
    database: dict[str, str]
    model_provider: str
    default_model: str
