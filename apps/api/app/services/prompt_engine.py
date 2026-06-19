from app.db import store
from app.models import ProblemSession, PromptRevision, PromptVariant
from app.schemas import (
    AnswerItem,
    ClarifyingQuestion,
    ClassificationResponse,
    PromptEngineRunResponse,
    PromptRevisionResponse,
    PromptSettings,
    PromptVariantResponse,
    RefinementMode,
)
from app.services.classifier import classify_problem
from app.services.guardrails import evaluate_guardrails
from app.services.profile_analyzer import get_prompt_profile
from app.services.prompt_generator import choose_prompt_strategies, generate_prompt_variants
from app.services.prompt_scorer import score_prompt_variants
from app.services.question_generator import generate_questions


def classification_for_session(session: ProblemSession) -> ClassificationResponse:
    if session.classification:
        existing = ClassificationResponse.model_validate(session.classification)
        if existing.domain_source in {"user_confirmed", "user_corrected"}:
            return existing
    return classify_problem(session.raw_input)


def needs_clarification(
    session: ProblemSession,
    classification: ClassificationResponse,
    profile_traits: list[dict] | None = None,
) -> bool:
    if classification.needs_domain_confirmation and classification.domain_source == "detected":
        return True
    required_question_ids = {
        question.id
        for question in generate_questions(
            session.raw_input,
            classification,
            profile_traits=profile_traits,
        )
        if question.required
    }
    handled_question_ids = {
        question.question_key
        for question in session.question_rows
        if question.answer_state in {"answered", "skipped"}
    }
    if not required_question_ids:
        return classification.confidence < 0.65
    return not required_question_ids.issubset(handled_question_ids)


def run_prompt_engine(
    session: ProblemSession,
    settings: PromptSettings,
    answers: list[AnswerItem] | None = None,
    mode: RefinementMode = "refinement",
) -> PromptEngineRunResponse:
    timeline: list[str] = []
    guardrail = evaluate_guardrails(session.raw_input)
    if guardrail.blocked:
        classification = classification_for_session(session)
        session.detected_domain = classification.domain
        session.detected_intent = classification.intent
        session.risk_level = classification.risk_level
        session.classification = classification.model_dump()
        session.touch("guardrail_blocked")
        session = store.upsert_session(session)
        timeline.append("guardrail_blocked")
        return PromptEngineRunResponse(
            session_id=session.id,
            mode=mode,
            classification=classification,
            needs_clarification=False,
            questions=[],
            prompts=[],
            recommended_prompt_id=None,
            assumptions=[],
            revisions=_revision_responses(session.id),
            timeline=timeline,
            guardrail_status="blocked",
            guardrail_message=guardrail.message,
            safe_redirect=guardrail.safe_redirect,
        )

    session.user_settings = settings.model_dump()
    classification = classification_for_session(session)
    session.detected_domain = classification.domain
    session.detected_intent = classification.intent
    session.risk_level = classification.risk_level
    session.classification = classification.model_dump()
    session.touch("classified")
    session = store.upsert_session(session)
    _persist_platform_preference(settings)
    timeline.append("classified")

    profile_traits = _profile_traits_for_refinement()
    questions = generate_questions(
        session.raw_input,
        classification,
        profile_traits=profile_traits,
    )
    session = store.replace_session_questions(session, questions)
    timeline.append("questions_ready")

    if answers:
        session = store.record_answers(session, answers)
        timeline.append("answers_recorded")

    clarify_needed = needs_clarification(
        session,
        classification,
        profile_traits=profile_traits,
    )
    assumption_sources = _assumption_sources_for_session(session)
    assumptions = [item["assumption"] for item in assumption_sources]

    if mode == "refinement" and clarify_needed:
        session.touch("clarification_pending")
        session = store.upsert_session(session)
        timeline.append("clarification_pending")
        return PromptEngineRunResponse(
            session_id=session.id,
            mode=mode,
            classification=classification,
            needs_clarification=True,
            questions=_questions_for_response(session),
            prompts=[],
            recommended_prompt_id=None,
            assumptions=assumptions,
            revisions=_revision_responses(session.id),
            timeline=timeline,
            guardrail_status="passed",
        )

    strategies = choose_prompt_strategies(session, settings, clarify_needed)
    previous_prompt = _previous_recommended_prompt(session)
    prompts = generate_prompt_variants(session, settings, strategies=strategies)
    prompts = store.replace_session_prompts(session, prompts)
    timeline.append("prompts_generated")

    scored = score_prompt_variants(
        problem=session.raw_input,
        prompts=prompts,
        settings=settings,
        risk_level=session.risk_level,
        needs_clarification=clarify_needed,
        missing_context_count=len(assumptions),
        recommendation_notes=_recommendation_notes(session, profile_traits),
        classification=classification,
        assumption_sources=assumption_sources,
        profile_traits=profile_traits,
        session_profile=_session_profile_metadata(session),
    )
    for prompt in scored:
        store.upsert_prompt(prompt)
    timeline.append("prompts_scored")

    recommended = next(
        (prompt.id for prompt in scored if prompt.recommendation_label == "recommended"),
        None,
    )
    recommended_prompt = next(
        (prompt for prompt in scored if prompt.id == recommended),
        scored[0] if scored else None,
    )
    if recommended_prompt:
        revision = store.record_prompt_revision(
            PromptRevision(
                session_id=session.id,
                prompt_variant_id=recommended_prompt.id,
                revision_type="refinement" if mode == "refinement" else "quick_generation",
                before_text=previous_prompt.prompt_text if previous_prompt else None,
                after_text=recommended_prompt.prompt_text,
                rationale=_revision_rationale(session, profile_traits, assumptions),
                revision_metadata={
                    "mode": mode,
                    "settings": settings.model_dump(),
                    "classification": classification.model_dump(),
                    "answered_question_ids": [
                        question.question_key
                        for question in session.question_rows
                        if question.answer_state == "answered"
                    ],
                    "skipped_question_ids": [
                        question.question_key
                        for question in session.question_rows
                        if question.answer_state == "skipped"
                    ],
                    "assumptions": assumptions,
                    "assumption_sources": assumption_sources,
                    "profile_traits": _profile_trait_metadata(profile_traits),
                    "session_profile": _session_profile_metadata(session),
                    "scorer_metadata": recommended_prompt.scorer_metadata,
                    "modification_audit_trail": recommended_prompt.modification_audit_trail,
                    "optimization_paths": recommended_prompt.optimization_paths,
                },
            )
        )
        timeline.append(f"revision_stored:{revision.id}")

    session.touch("ready")
    store.upsert_session(session)
    timeline.append("ready")

    return PromptEngineRunResponse(
        session_id=session.id,
        mode=mode,
        classification=classification,
        needs_clarification=clarify_needed,
        questions=_questions_for_response(session),
        prompts=[PromptVariantResponse.model_validate(prompt) for prompt in scored],
        recommended_prompt_id=recommended,
        assumptions=assumptions,
        revisions=_revision_responses(session.id),
        timeline=timeline,
        guardrail_status="passed",
    )


def _questions_for_response(session: ProblemSession) -> list[ClarifyingQuestion]:
    return [
        ClarifyingQuestion.model_validate(question)
        for question in session.clarifying_questions
    ]


def _previous_recommended_prompt(session: ProblemSession) -> PromptVariant | None:
    prompts = store.get_session_prompts(session)
    return next(
        (prompt for prompt in prompts if prompt.recommendation_label == "recommended"),
        prompts[0] if prompts else None,
    )


def _assumptions_for_session(session: ProblemSession) -> list[str]:
    return [item["assumption"] for item in _assumption_sources_for_session(session)]


def _assumption_sources_for_session(session: ProblemSession) -> list[dict]:
    return [
        {
            "question_id": question.question_key,
            "question": question.question,
            "state": question.answer_state,
            "assumption": f"{question.question_key.replace('_', ' ')} is unspecified",
            "reason": question.reason,
        }
        for question in session.question_rows
        if question.required and question.answer_state in {"skipped", "unanswered"}
    ]


def _profile_traits_for_refinement() -> list[dict]:
    try:
        profile = get_prompt_profile()
    except Exception:
        return []
    traits = [
        {
            "trait_key": trait.trait_key,
            "trait_label": trait.trait_label,
            "score": trait.score,
            "confidence": trait.confidence,
            "evidence_level": trait.evidence_level,
            "signal_count": trait.signal_count,
            "summary": trait.summary,
        }
        for trait in profile.traits
        if trait.signal_count > 0 and trait.evidence_level != "none"
    ]
    return sorted(
        traits,
        key=lambda trait: (trait["confidence"], trait["score"], trait["signal_count"]),
        reverse=True,
    )


def _recommendation_notes(
    session: ProblemSession,
    profile_traits: list[dict],
) -> list[str]:
    answered_count = sum(
        1 for question in session.question_rows if question.answer_state == "answered"
    )
    skipped_count = sum(
        1 for question in session.question_rows if question.answer_state == "skipped"
    )
    notes = [
        f"{session.user_settings.get('target_platform', 'generic')} platform",
        f"{answered_count} clarifying answers",
        f"{skipped_count} skipped questions",
    ]
    classification = session.classification or {}
    domain_source = classification.get("domain_source")
    if domain_source in {"user_confirmed", "user_corrected"}:
        notes.append("confirmed domain")
    if profile_traits:
        for trait in profile_traits[:2]:
            notes.append(
                f"profile trait {trait['trait_label']} "
                f"{round(float(trait['score']) * 100)}"
            )
    else:
        notes.append("no profile traits yet")
    return notes


def _persist_platform_preference(settings: PromptSettings) -> None:
    platform = settings.target_platform
    confidence = 0.82 if platform != "generic" else 0.56
    store.upsert_platform_preference(
        platform=platform,
        preference=settings.model_dump(),
        confidence=confidence,
    )


def _revision_rationale(
    session: ProblemSession,
    profile_traits: list[dict],
    assumptions: list[str],
) -> str:
    answered_count = sum(
        1 for question in session.question_rows if question.answer_state == "answered"
    )
    skipped_count = sum(
        1 for question in session.question_rows if question.answer_state == "skipped"
    )
    profile_note = (
        f" Profile signals used: {', '.join(trait['trait_label'] for trait in profile_traits[:2])}."
        if profile_traits
        else " No profile traits were available yet."
    )
    assumption_note = (
        f" {len(assumptions)} assumptions were carried into the prompt."
        if assumptions
        else " No required assumptions were carried forward."
    )
    return (
        f"Refined from {answered_count} answered and {skipped_count} skipped clarifying questions."
        f"{profile_note}{assumption_note}"
    )


def _profile_trait_metadata(profile_traits: list[dict]) -> list[dict]:
    return [
        {
            "trait_key": trait["trait_key"],
            "trait_label": trait["trait_label"],
            "score": trait["score"],
            "confidence": trait["confidence"],
            "evidence_level": trait["evidence_level"],
            "signal_count": trait["signal_count"],
        }
        for trait in profile_traits[:4]
    ]


def _revision_responses(session_id: str) -> list[PromptRevisionResponse]:
    return [
        PromptRevisionResponse.model_validate(revision)
        for revision in store.list_prompt_revisions(session_id)[:5]
    ]


def _session_profile_metadata(session: ProblemSession) -> dict:
    return {
        "display_name": session.display_name,
        "primary_ai_platform": session.primary_ai_platform,
        "rules_accepted": session.rules_accepted,
    }
