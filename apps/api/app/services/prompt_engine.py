from app.db import store
from app.models import ProblemSession
from app.schemas import (
    AnswerItem,
    ClassificationResponse,
    PromptEngineRunResponse,
    PromptSettings,
    PromptVariantResponse,
)
from app.services.classifier import classify_problem
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
) -> bool:
    answered = set(session.answers)
    required_question_ids = {
        question.id
        for question in generate_questions(session.raw_input, classification)
        if question.required
    }
    if not required_question_ids:
        return classification.confidence < 0.65
    return not required_question_ids.issubset(answered)


def run_prompt_engine(
    session: ProblemSession,
    settings: PromptSettings,
    answers: list[AnswerItem] | None = None,
) -> PromptEngineRunResponse:
    timeline: list[str] = []

    session.user_settings = settings.model_dump()
    classification = classification_for_session(session)
    session.detected_domain = classification.domain
    session.detected_intent = classification.intent
    session.risk_level = classification.risk_level
    session.classification = classification.model_dump()
    session.touch("classified")
    session = store.upsert_session(session)
    timeline.append("classified")

    questions = generate_questions(session.raw_input, classification)
    session = store.replace_session_questions(session, questions)
    timeline.append("questions_ready")

    if answers:
        session = store.record_answers(session, answers)
        timeline.append("answers_recorded")

    clarify_needed = needs_clarification(session, classification)
    strategies = choose_prompt_strategies(session, settings, clarify_needed)
    prompts = generate_prompt_variants(session, settings, strategies=strategies)
    prompts = store.replace_session_prompts(session, prompts)
    timeline.append("prompts_generated")

    scored = score_prompt_variants(
        problem=session.raw_input,
        prompts=prompts,
        settings=settings,
        risk_level=session.risk_level,
        needs_clarification=clarify_needed,
    )
    for prompt in scored:
        store.upsert_prompt(prompt)
    timeline.append("prompts_scored")

    recommended = next(
        (prompt.id for prompt in scored if prompt.recommendation_label == "recommended"),
        None,
    )
    session.touch("ready")
    store.upsert_session(session)
    timeline.append("ready")

    return PromptEngineRunResponse(
        session_id=session.id,
        classification=classification,
        needs_clarification=clarify_needed,
        questions=questions,
        prompts=[PromptVariantResponse.model_validate(prompt) for prompt in scored],
        recommended_prompt_id=recommended,
        timeline=timeline,
    )
