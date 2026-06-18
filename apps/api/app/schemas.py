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
TargetPlatform = Literal["codex", "claude", "chatgpt", "gemini", "cursor", "generic"]
DetailLevel = Literal["concise", "balanced", "exhaustive"]
Formality = Literal["casual", "neutral", "formal"]
TemperaturePreference = Literal["precise", "balanced", "creative"]
ReasoningStyle = Literal["direct_answer", "step_by_step", "ask_first", "explore_options"]
SourceStrictness = Literal["none", "cite_when_needed", "official_only", "evidence_first"]
InteractionMode = Literal["one_shot", "iterative", "agentic"]
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


class CreateSessionRequest(BaseModel):
    raw_input: str = Field(..., min_length=3)
    settings: PromptSettings = Field(default_factory=PromptSettings)


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
    raw_input: str
    detected_domain: str | None
    detected_intent: str | None
    risk_level: str | None
    user_settings: dict
    status: str
    clarifying_questions: list[dict] = Field(default_factory=list)
    answers: dict[str, str] = Field(default_factory=dict)
    prompt_variant_ids: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


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
    created_at: datetime
    updated_at: datetime


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
