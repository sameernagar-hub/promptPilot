from dataclasses import dataclass
from typing import Any

from app.db import store
from app.models import CoachingObservation, ProblemSession, PromptVariant
from app.schemas import CoachingObservationResponse


@dataclass(frozen=True)
class HabitDefinition:
    habit_id: str
    label: str
    applied_fix: str
    confidence: float
    relevant_domains: set[str] | None = None
    relevant_intents: set[str] | None = None


HABITS = [
    HabitDefinition(
        habit_id="missing_success_criteria",
        label="Missing success criteria",
        applied_fix=(
            "Added a definition of success so the assistant knows what a good finished answer should satisfy."
        ),
        confidence=0.82,
        relevant_intents={"build", "troubleshoot", "plan", "write"},
    ),
    HabitDefinition(
        habit_id="missing_target_audience",
        label="Missing target audience",
        applied_fix=(
            "Added an audience assumption so tone, examples, and depth have a clear default."
        ),
        confidence=0.76,
        relevant_domains={
            "writing_communication",
            "creative_media",
            "learning_research",
            "business_strategy",
            "hobby_project",
            "general_problem_solving",
        },
    ),
    HabitDefinition(
        habit_id="missing_output_constraints",
        label="Missing output constraints",
        applied_fix=(
            "Added output structure and practical constraints so the result is easier to use."
        ),
        confidence=0.78,
    ),
]

SUCCESS_TERMS = {
    "acceptance criteria",
    "definition of done",
    "done when",
    "finished when",
    "good if",
    "success",
    "success criteria",
    "should include",
    "should look like",
}

AUDIENCE_TERMS = {
    "audience",
    "beginners",
    "children",
    "client",
    "customers",
    "experts",
    "for a class",
    "for beginners",
    "for kids",
    "for my boss",
    "for my team",
    "for parents",
    "for students",
    "reader",
    "students",
    "team",
    "users",
    "viewers",
}

OUTPUT_CONSTRAINT_TERMS = {
    "bullet",
    "bullets",
    "checklist",
    "diagram",
    "format",
    "markdown",
    "one page",
    "outline",
    "table",
    "template",
    "under ",
}


def attach_coaching_observations(
    session: ProblemSession,
    prompts: list[PromptVariant],
) -> list[PromptVariant]:
    recommended = next(
        (prompt for prompt in prompts if prompt.recommendation_label == "recommended"),
        prompts[0] if prompts else None,
    )
    if recommended is None:
        return prompts

    observations = _detect_observations(session, recommended.id)
    stored = store.replace_session_coaching_observations(session.id, observations)
    payloads = [
        CoachingObservationResponse.model_validate(observation).model_dump(mode="json")
        for observation in stored
    ]
    for prompt in prompts:
        metadata = dict(prompt.score_metadata or {})
        metadata["coaching_observations"] = payloads if prompt.id == recommended.id else []
        prompt.score_metadata = metadata
    return prompts


def _detect_observations(
    session: ProblemSession,
    prompt_variant_id: str,
) -> list[CoachingObservation]:
    raw_input = _clean(session.raw_input)
    lowered = raw_input.lower()
    domain = _domain_for_session(session)
    intent = _intent_for_session(session)
    observations: list[CoachingObservation] = []
    for habit in HABITS:
        if not _habit_applies(habit, domain, intent):
            continue
        if habit.habit_id == "missing_success_criteria" and _contains_any(lowered, SUCCESS_TERMS):
            continue
        if habit.habit_id == "missing_target_audience" and _contains_any(lowered, AUDIENCE_TERMS):
            continue
        if habit.habit_id == "missing_output_constraints" and _contains_any(
            lowered,
            OUTPUT_CONSTRAINT_TERMS,
        ):
            continue
        source_session_ids = [
            session.id,
            *store.recent_coaching_session_ids(habit.habit_id, session.id, limit=2),
        ]
        observations.append(
            CoachingObservation(
                session_id=session.id,
                prompt_variant_id=prompt_variant_id,
                habit_id=habit.habit_id,
                habit_label=habit.label,
                evidence_excerpt=_evidence_excerpt(raw_input, habit.habit_id),
                source_session_ids=source_session_ids,
                confidence=habit.confidence,
                applied_fix=habit.applied_fix,
                user_feedback="unset",
            )
        )
    return observations[:3]


def _habit_applies(habit: HabitDefinition, domain: str, intent: str) -> bool:
    if habit.relevant_domains is not None and domain not in habit.relevant_domains:
        return False
    if habit.relevant_intents is not None and intent not in habit.relevant_intents:
        return False
    return True


def _domain_for_session(session: ProblemSession) -> str:
    classification: dict[str, Any] = session.classification or {}
    return str(session.detected_domain or classification.get("domain") or "general_problem_solving")


def _intent_for_session(session: ProblemSession) -> str:
    classification: dict[str, Any] = session.classification or {}
    intent = str(session.detected_intent or classification.get("intent") or "clarify_and_plan")
    return {
        "create": "build",
        "diagnose": "troubleshoot",
        "fix": "troubleshoot",
    }.get(intent, intent)


def _contains_any(text: str, terms: set[str]) -> bool:
    return any(term in text for term in terms)


def _evidence_excerpt(raw_input: str, habit_id: str) -> str:
    excerpt = raw_input if len(raw_input) <= 180 else f"{raw_input[:177]}..."
    gap = {
        "missing_success_criteria": "No explicit success criterion or definition of done was stated.",
        "missing_target_audience": "No target audience was stated.",
        "missing_output_constraints": "No concrete output format, length, or structure constraint was stated.",
    }[habit_id]
    return f"{gap} Request excerpt: {excerpt}"


def _clean(value: str) -> str:
    return " ".join(value.strip().split())
