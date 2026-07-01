import json
from typing import Literal

from fastapi import APIRouter, HTTPException

from app.db import store
from app.schemas import (
    AuditLogResponse,
    ClarifyingQuestionsResponse,
    ClassificationResponse,
    CoachingFeedbackRequest,
    CoachingObservationResponse,
    CreateSessionRequest,
    DeleteSessionDataResponse,
    DomainConfirmationRequest,
    DomainConfirmationResponse,
    EndSessionResponse,
    GeneratePromptsRequest,
    PromptEngineRunRequest,
    PromptEngineRunResponse,
    PromptRevisionResponse,
    PromptSettings,
    PromptVariantResponse,
    RunPromptRequest,
    RunPromptResponse,
    ScorePromptsResponse,
    SessionExportResponse,
    SessionResponse,
    SubmitAnswersRequest,
)
from app.services.classifier import apply_domain_confirmation, classify_problem
from app.services.coaching_habits import attach_coaching_observations
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


def _session_response(session) -> SessionResponse:
    prompts = store.get_session_prompts(session)
    response = SessionResponse.model_validate(session)
    response.prompts = [PromptVariantResponse.model_validate(prompt) for prompt in prompts]
    response.recommended_prompt_id = next(
        (prompt.id for prompt in prompts if prompt.recommendation_label == "recommended"),
        prompts[0].id if prompts else None,
    )
    response.revisions = [
        PromptRevisionResponse.model_validate(revision)
        for revision in store.list_prompt_revisions(session.id)[:5]
    ]
    return response


@router.post("", response_model=SessionResponse, status_code=201)
def create_session(payload: CreateSessionRequest) -> SessionResponse:
    session = store.create_session(
        raw_input=payload.raw_input,
        user_settings=payload.settings.model_dump(),
        display_name=payload.display_name,
        primary_ai_platform=payload.primary_ai_platform,
        rules_accepted=payload.rules_accepted,
        session_metadata=payload.session_metadata,
    )
    return _session_response(session)


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str) -> SessionResponse:
    session = _get_session_or_404(session_id)
    return _session_response(session)


@router.post("/{session_id}/end", response_model=EndSessionResponse)
def end_session(session_id: str) -> EndSessionResponse:
    session = _get_session_or_404(session_id)
    ended = store.end_session(session.id)
    if ended.ended_at is None:
        raise HTTPException(status_code=500, detail="Session end timestamp missing")
    return EndSessionResponse(id=ended.id, status=ended.status, ended_at=ended.ended_at)


@router.get("/{session_id}/audit-logs", response_model=list[AuditLogResponse])
def list_session_audit_logs(session_id: str) -> list[AuditLogResponse]:
    _get_session_or_404(session_id)
    return [
        AuditLogResponse.model_validate(row)
        for row in store.list_session_audit_logs(session_id)
    ]


@router.get("/{session_id}/export", response_model=SessionExportResponse)
def export_session(
    session_id: str,
    format: Literal["markdown", "json"] = "markdown",
) -> SessionExportResponse:
    session = _get_session_or_404(session_id)
    prompts = store.get_session_prompts(session)
    audit_logs = store.list_session_audit_logs(session.id)
    payload = _session_export_payload(session, prompts, audit_logs)
    if format == "json":
        content = json.dumps(payload, indent=2, default=str)
        filename = f"promptpilot-session-{session.id}.json"
    else:
        content = _session_export_markdown(payload)
        filename = f"promptpilot-session-{session.id}.md"
    store.record_audit_log(
        event_type="session_exported",
        entity_type="problem_session",
        entity_id=session.id,
        session_id=session.id,
        metadata={"format": format, "prompt_count": len(prompts)},
    )
    return SessionExportResponse(
        session_id=session.id,
        format=format,
        filename=filename,
        content=content,
        metadata={
            "prompt_count": len(prompts),
            "audit_event_count": len(audit_logs),
            "status": session.status,
        },
    )


@router.delete("/{session_id}/data", response_model=DeleteSessionDataResponse)
def delete_session_data(session_id: str) -> DeleteSessionDataResponse:
    _get_session_or_404(session_id)
    deleted_counts = store.delete_session_data(session_id)
    return DeleteSessionDataResponse(
        session_id=session_id,
        deleted=True,
        deleted_counts=deleted_counts,
    )


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
    store.record_audit_log(
        event_type="classification_run",
        entity_type="problem_session",
        entity_id=session.id,
        session_id=session.id,
        metadata={
            "domain": classification.domain,
            "intent": classification.intent,
            "risk_level": classification.risk_level,
            "confidence": classification.confidence,
        },
    )
    return classification


@router.post("/{session_id}/domain-confirmation", response_model=DomainConfirmationResponse)
def confirm_session_domain(
    session_id: str,
    payload: DomainConfirmationRequest,
) -> DomainConfirmationResponse:
    session = _get_session_or_404(session_id)
    classification = (
        ClassificationResponse.model_validate(session.classification)
        if session.classification
        else classify_problem(session.raw_input)
    )
    confirmed = apply_domain_confirmation(
        classification,
        confirmed_domain=payload.confirmed_domain,
        accepted=payload.accepted,
    )
    session = store.confirm_session_domain(
        session_id=session.id,
        classification=confirmed.model_dump(),
        confirmed_domain=confirmed.domain,
        domain_source=confirmed.domain_source,
        confidence=confirmed.confidence,
        evidence=confirmed.evidence,
    )
    store.record_audit_log(
        event_type="domain_confirmed",
        entity_type="problem_session",
        entity_id=session.id,
        session_id=session.id,
        metadata={
            "domain": confirmed.domain,
            "domain_source": confirmed.domain_source,
            "confidence": confirmed.confidence,
        },
    )
    return DomainConfirmationResponse(
        session_id=session.id,
        classification=ClassificationResponse.model_validate(session.classification),
    )


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
    store.record_audit_log(
        event_type="clarifying_questions_generated",
        entity_type="problem_session",
        entity_id=session.id,
        session_id=session.id,
        metadata={"question_count": len(questions)},
    )
    return ClarifyingQuestionsResponse(session_id=session.id, questions=questions)


@router.post("/{session_id}/answers", response_model=SessionResponse)
def submit_answers(
    session_id: str,
    payload: SubmitAnswersRequest,
) -> SessionResponse:
    session = _get_session_or_404(session_id)
    session = store.record_answers(session, payload.answers)
    store.record_audit_log(
        event_type="clarifying_answers_recorded",
        entity_type="problem_session",
        entity_id=session.id,
        session_id=session.id,
        metadata={
            "answered_count": sum(1 for answer in payload.answers if answer.state == "answered"),
            "skipped_count": sum(1 for answer in payload.answers if answer.state == "skipped"),
        },
    )
    return _session_response(session)


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
    store.record_audit_log(
        event_type="prompt_generation_run",
        entity_type="problem_session",
        entity_id=session.id,
        session_id=session.id,
        metadata={"prompt_count": len(prompts), "target_platform": settings.target_platform},
    )
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
    scored = attach_coaching_observations(session, scored)
    for prompt in scored:
        store.upsert_prompt(prompt)

    session.touch("prompts_scored")
    session = store.upsert_session(session)
    recommended = next(
        (prompt.id for prompt in scored if prompt.recommendation_label == "recommended"),
        None,
    )
    recommended_prompt = next((prompt for prompt in scored if prompt.id == recommended), None)
    store.record_audit_log(
        event_type="scorer_run",
        entity_type="problem_session",
        entity_id=session.id,
        session_id=session.id,
        metadata={
            "prompt_count": len(scored),
            "recommended_prompt_id": recommended,
            "scorer_metadata": recommended_prompt.scorer_metadata if recommended_prompt else {},
        },
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
    mode = payload.mode if payload else "refinement"
    response = run_prompt_engine(session, settings=settings, answers=answers, mode=mode)
    if response.guardrail_status == "blocked":
        store.record_audit_log(
            event_type="guardrail_blocked",
            entity_type="problem_session",
            entity_id=session.id,
            session_id=session.id,
            metadata={
                "message": response.guardrail_message,
                "safe_redirect": response.safe_redirect,
            },
        )
    elif response.prompts:
        recommended_prompt = next(
            (prompt for prompt in response.prompts if prompt.id == response.recommended_prompt_id),
            response.prompts[0],
        )
        store.record_audit_log(
            event_type="scorer_run",
            entity_type="problem_session",
            entity_id=session.id,
            session_id=session.id,
            metadata={
                "mode": response.mode,
                "prompt_count": len(response.prompts),
                "recommended_prompt_id": response.recommended_prompt_id,
                "scorer_metadata": recommended_prompt.scorer_metadata,
                "assumption_count": len(response.assumptions),
            },
        )
    return response


@router.patch(
    "/{session_id}/coaching-observations/{observation_id}",
    response_model=CoachingObservationResponse,
)
def update_coaching_observation_feedback(
    session_id: str,
    observation_id: str,
    payload: CoachingFeedbackRequest,
) -> CoachingObservationResponse:
    _get_session_or_404(session_id)
    observation = store.update_coaching_feedback(
        observation_id=observation_id,
        session_id=session_id,
        feedback=payload.feedback,
    )
    if observation is None:
        raise HTTPException(status_code=404, detail="Coaching observation not found")
    store.record_audit_log(
        event_type="coaching_feedback_recorded",
        entity_type="coaching_observation",
        entity_id=observation.id,
        session_id=session_id,
        metadata={
            "habit_id": observation.habit_id,
            "feedback": observation.user_feedback,
        },
    )
    return CoachingObservationResponse.model_validate(observation)


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

    response = run_prompt(prompt)
    store.record_audit_log(
        event_type="model_run_previewed",
        entity_type="prompt_variant",
        entity_id=prompt.id,
        session_id=session.id,
        metadata={
            "provider": response.provider,
            "model": response.model,
            "prompt_id": prompt.id,
        },
    )
    return response


def _session_export_payload(session, prompts, audit_logs) -> dict:
    return {
        "session": {
            "id": session.id,
            "display_name": session.display_name,
            "primary_ai_platform": session.primary_ai_platform,
            "status": session.status,
            "raw_input": session.raw_input,
            "detected_domain": session.detected_domain,
            "detected_intent": session.detected_intent,
            "risk_level": session.risk_level,
            "classification": session.classification,
            "settings": session.user_settings,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "ended_at": session.ended_at,
        },
        "questions": session.clarifying_questions,
        "answers": session.answers,
        "prompts": [
            {
                "id": prompt.id,
                "title": prompt.title,
                "strategy": prompt.strategy,
                "recommendation_label": prompt.recommendation_label,
                "score_total": prompt.score_total,
                "score_breakdown": prompt.score_breakdown,
                "score_metadata": prompt.score_metadata,
                "prompt_text": prompt.prompt_text,
                "created_at": prompt.created_at,
            }
            for prompt in prompts
        ],
        "audit_logs": [
            {
                "id": row.id,
                "event_type": row.event_type,
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "metadata": row.event_metadata,
                "created_at": row.created_at,
            }
            for row in audit_logs
        ],
    }


def _session_export_markdown(payload: dict) -> str:
    session = payload["session"]
    lines = [
        f"# PromptPilot Session {session['id']}",
        "",
        f"- Display name: {session.get('display_name') or 'Unspecified'}",
        f"- Platform: {session.get('primary_ai_platform') or 'Unspecified'}",
        f"- Status: {session.get('status')}",
        f"- Domain: {session.get('detected_domain') or 'Unclassified'}",
        f"- Intent: {session.get('detected_intent') or 'Unclassified'}",
        "",
        "## Original Request",
        "",
        str(session.get("raw_input") or ""),
        "",
        "## Clarifying Context",
        "",
    ]
    questions = payload.get("questions") or []
    if questions:
        for question in questions:
            state = question.get("state", "unanswered")
            answer = question.get("answer") or "No answer recorded"
            lines.append(f"- {question.get('question')} ({state}): {answer}")
    else:
        lines.append("No clarifying questions were recorded.")
    lines.extend(["", "## Prompts", ""])
    prompts = payload.get("prompts") or []
    if prompts:
        for prompt in prompts:
            lines.extend(
                [
                    f"### {prompt.get('title')} ({prompt.get('recommendation_label')})",
                    "",
                    f"Score: {prompt.get('score_total') or 'Not scored'}",
                    "",
                    "```text",
                    str(prompt.get("prompt_text") or ""),
                    "```",
                    "",
                ]
            )
    else:
        lines.append("No prompts were generated.")
    lines.extend(["", "## Audit Events", ""])
    audit_logs = payload.get("audit_logs") or []
    if audit_logs:
        for row in audit_logs:
            lines.append(f"- {row.get('created_at')}: {row.get('event_type')}")
    else:
        lines.append("No audit events were recorded.")
    lines.append("")
    return "\n".join(lines)
