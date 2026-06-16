from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


PromptLength = Literal["short", "medium", "deep"]
SkillLevel = Literal["beginner", "practical", "expert"]
Tone = Literal["direct", "friendly", "technical"]
PromptFormat = Literal["checklist", "guide", "table", "conversation", "plan"]
RiskPreference = Literal["safe_only", "normal", "advanced"]
SourcePreference = Literal["none", "web", "official_docs"]


class PromptSettings(BaseModel):
    length: PromptLength = "medium"
    skill_level: SkillLevel = "practical"
    tone: Tone = "friendly"
    format: PromptFormat = "guide"
    risk: RiskPreference = "normal"
    sources: SourcePreference = "none"


class CreateSessionRequest(BaseModel):
    raw_input: str = Field(..., min_length=3)
    settings: PromptSettings = Field(default_factory=PromptSettings)


class ClassificationResponse(BaseModel):
    domain: str
    intent: str
    risk_level: str
    confidence: float
    signals: list[str] = Field(default_factory=list)


class ClarifyingQuestion(BaseModel):
    id: str
    question: str
    reason: str
    required: bool = True


class ClarifyingQuestionsResponse(BaseModel):
    session_id: str
    questions: list[ClarifyingQuestion]


class AnswerItem(BaseModel):
    question_id: str
    answer: str = Field(..., min_length=1)


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


class PromptEngineRunResponse(BaseModel):
    session_id: str
    classification: ClassificationResponse
    needs_clarification: bool
    questions: list[ClarifyingQuestion]
    prompts: list[PromptVariantResponse]
    recommended_prompt_id: str | None
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


class HealthResponse(BaseModel):
    service: str
    status: str
    database: dict[str, str]
    model_provider: str
    default_model: str
