from fastapi import APIRouter, HTTPException

from app.db import store
from app.schemas import (
    ClarifyingQuestionsResponse,
    ClassificationResponse,
    CreateSessionRequest,
    GeneratePromptsRequest,
    PromptEngineRunRequest,
    PromptEngineRunResponse,
    PromptSettings,
    PromptVariantResponse,
    RunPromptRequest,
    RunPromptResponse,
    ScorePromptsResponse,
    SessionResponse,
    SubmitAnswersRequest,
)
from app.services.classifier import classify_problem
from app.services.llm_client import run_prompt
from app.services.prompt_engine import run_prompt_engine
from app.services.prompt_generator import generate_prompt_variants
from app.services.prompt_scorer import score_prompt_variants
from app.services.question_generator import generate_questions


router = APIRouter(prefix="/sessions", tags=["sessions"])


def _get_session_or_404(session_id: str):
    session = store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def _settings_from_session(session) -> PromptSettings:
    return PromptSettings.model_validate(session.user_settings)


@router.post("", response_model=SessionResponse, status_code=201)
def create_session(payload: CreateSessionRequest) -> SessionResponse:
    session = store.create_session(
        raw_input=payload.raw_input,
        user_settings=payload.settings.model_dump(),
    )
    return SessionResponse.model_validate(session)


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str) -> SessionResponse:
    session = _get_session_or_404(session_id)
    return SessionResponse.model_validate(session)


@router.post("/{session_id}/classify", response_model=ClassificationResponse)
def classify_session(session_id: str) -> ClassificationResponse:
    session = _get_session_or_404(session_id)
    classification = classify_problem(session.raw_input)
    session.detected_domain = classification.domain
    session.detected_intent = classification.intent
    session.risk_level = classification.risk_level
    session.classification = classification.model_dump()
    session.touch("classified")
    store.upsert_session(session)
    return classification


@router.post("/{session_id}/questions", response_model=ClarifyingQuestionsResponse)
def create_questions(session_id: str) -> ClarifyingQuestionsResponse:
    session = _get_session_or_404(session_id)
    classification = (
        classify_problem(session.raw_input)
        if session.classification is None
        else ClassificationResponse.model_validate(session.classification)
    )
    if session.classification is None:
        session.detected_domain = classification.domain
        session.detected_intent = classification.intent
        session.risk_level = classification.risk_level
        session.classification = classification.model_dump()
        session = store.upsert_session(session)

    questions = generate_questions(session.raw_input, classification)
    store.replace_session_questions(session, questions)
    return ClarifyingQuestionsResponse(session_id=session.id, questions=questions)


@router.post("/{session_id}/answers", response_model=SessionResponse)
def submit_answers(
    session_id: str,
    payload: SubmitAnswersRequest,
) -> SessionResponse:
    session = _get_session_or_404(session_id)
    session = store.record_answers(session, payload.answers)
    return SessionResponse.model_validate(session)


@router.post("/{session_id}/generate-prompts", response_model=list[PromptVariantResponse])
def generate_prompts(
    session_id: str,
    payload: GeneratePromptsRequest | None = None,
) -> list[PromptVariantResponse]:
    session = _get_session_or_404(session_id)
    settings = payload.settings if payload and payload.settings else _settings_from_session(session)
    session.user_settings = settings.model_dump()

    if session.classification is None:
        classification = classify_problem(session.raw_input)
        session.detected_domain = classification.domain
        session.detected_intent = classification.intent
        session.risk_level = classification.risk_level
        session.classification = classification.model_dump()
    session = store.upsert_session(session)

    prompts = generate_prompt_variants(session, settings)
    store.replace_session_prompts(session, prompts)
    return [PromptVariantResponse.model_validate(prompt) for prompt in prompts]


@router.post("/{session_id}/score-prompts", response_model=ScorePromptsResponse)
def score_prompts(session_id: str) -> ScorePromptsResponse:
    session = _get_session_or_404(session_id)
    prompts = store.get_session_prompts(session)
    if not prompts:
        raise HTTPException(status_code=400, detail="Generate prompts before scoring")

    scored = score_prompt_variants(
        problem=session.raw_input,
        prompts=prompts,
        settings=_settings_from_session(session),
    )
    for prompt in scored:
        store.upsert_prompt(prompt)

    session.touch("prompts_scored")
    session = store.upsert_session(session)
    recommended = next(
        (prompt.id for prompt in scored if prompt.recommendation_label == "recommended"),
        None,
    )
    return ScorePromptsResponse(
        session_id=session.id,
        prompts=[PromptVariantResponse.model_validate(prompt) for prompt in scored],
        recommended_prompt_id=recommended,
    )


@router.post("/{session_id}/run-pipeline", response_model=PromptEngineRunResponse)
def run_session_pipeline(
    session_id: str,
    payload: PromptEngineRunRequest | None = None,
) -> PromptEngineRunResponse:
    session = _get_session_or_404(session_id)
    settings = payload.settings if payload and payload.settings else _settings_from_session(session)
    answers = payload.answers if payload else []
    return run_prompt_engine(session, settings=settings, answers=answers)


@router.post("/{session_id}/run-prompt", response_model=RunPromptResponse)
def run_session_prompt(
    session_id: str,
    payload: RunPromptRequest | None = None,
) -> RunPromptResponse:
    session = _get_session_or_404(session_id)
    prompts = store.get_session_prompts(session)
    if not prompts:
        raise HTTPException(status_code=400, detail="Generate prompts before running one")

    prompt_id = payload.prompt_id if payload and payload.prompt_id else None
    prompt = store.get_prompt(prompt_id) if prompt_id else None
    if prompt_id and prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    if prompt is None:
        prompt = next(
            (item for item in prompts if item.recommendation_label == "recommended"),
            prompts[0],
        )
    if prompt.session_id != session.id:
        raise HTTPException(status_code=400, detail="Prompt does not belong to this session")

    return run_prompt(prompt)
