from collections import Counter
from statistics import mean
from typing import Any

from sqlalchemy import select

from app.db import SessionLocal
from app.models import (
    ProblemSession,
    ProfileObservationOverride,
    PromptRevision,
    TraitObservation,
    utc_now,
)
from app.schemas import (
    ProfileEvidenceReference,
    ProfileInsightItem,
    ProfileInsightsResponse,
    ProfileObservationDeleteResponse,
    ProfileObservationUpdateRequest,
    ProfileQuestionRequest,
    ProfileQuestionResponse,
    PromptProfileResponse,
    TraitObservationResponse,
)
from app.services.profile_analyzer import ensure_local_profile, get_prompt_profile


SUGGESTED_QUESTIONS = [
    "What do I usually forget to include?",
    "Why do my prompts get vague answers?",
    "How should I prompt Codex better?",
    "What tone do I usually prefer?",
    "Which domains do I ask about most?",
    "How can I make my research prompts stronger?",
]


def get_profile_insights() -> ProfileInsightsResponse:
    profile = get_prompt_profile()
    with SessionLocal() as database:
        sessions = list(
            database.scalars(
                select(ProblemSession).order_by(ProblemSession.created_at.desc())
            )
        )
        revisions = list(
            database.scalars(
                select(PromptRevision)
                .order_by(PromptRevision.created_at.desc())
                .limit(6)
            )
        )

    traits = {trait.trait_key: trait for trait in profile.traits}
    empty_state = None
    if profile.status == "empty" or profile.summary.get("needs_more_evidence"):
        empty_state = (
            "Profile guidance is still tentative. Add a few workspace sessions or "
            "chat imports so answers can cite stronger evidence."
        )

    return ProfileInsightsResponse(
        profile_status=profile.status,
        headline=profile.summary.get("headline", "Profile evidence is still forming."),
        common_missing_details=_missing_detail_items(traits, profile),
        preferences=_preference_items(profile, sessions, traits),
        frequent_domains=_domain_items(sessions),
        platform_advice=_platform_items(profile, traits),
        recent_revisions=_revision_items(revisions),
        suggested_questions=SUGGESTED_QUESTIONS,
        empty_state=empty_state,
    )


def answer_profile_question(payload: ProfileQuestionRequest) -> ProfileQuestionResponse:
    question = payload.question.strip()
    profile = get_prompt_profile()
    insights = get_profile_insights()
    traits = {trait.trait_key: trait for trait in profile.traits}
    lowered = question.lower()

    if profile.status == "empty" or not profile.traits:
        return ProfileQuestionResponse(
            question=question,
            answer=(
                "I do not have enough prompting evidence yet to answer that reliably. "
                "Create a few sessions or import representative chats, then refresh "
                "the profile so I can cite real examples."
            ),
            confidence=0.15,
            evidence_level="none",
            suggested_followups=SUGGESTED_QUESTIONS[:3],
            needs_more_evidence=True,
        )

    if _matches(lowered, {"forget", "missing", "include", "vague", "vagueness"}):
        selected = _select_traits(
            traits,
            [
                "missing_context_patterns",
                "context_depth",
                "constraint_specificity",
                "goal_clarity",
                "source_expectation",
            ],
        )
        answer = _missing_answer(selected, insights.common_missing_details)
    elif _matches(lowered, {"codex", "cursor", "platform", "repo", "code"}):
        selected = _select_traits(
            traits,
            ["technical_depth", "constraint_specificity", "context_depth", "iteration_style"],
        )
        answer = _codex_answer(selected, insights.platform_advice)
    elif _matches(lowered, {"tone", "format", "prefer", "preference", "detail"}):
        selected = _select_traits(
            traits,
            ["tone_preference", "format_preference", "formality_preference", "context_depth"],
        )
        answer = _preference_answer(selected, insights.preferences)
    elif _matches(lowered, {"domain", "domains", "topic", "topics", "task", "tasks"}):
        selected = _select_traits(traits, ["domain_precision", "technical_depth"])
        answer = _domain_answer(selected, insights.frequent_domains)
    elif _matches(lowered, {"research", "source", "sources", "cite", "evidence"}):
        selected = _select_traits(
            traits,
            ["source_expectation", "constraint_specificity", "context_depth", "goal_clarity"],
        )
        answer = _research_answer(selected)
    else:
        selected = sorted(
            traits.values(),
            key=lambda trait: (trait.confidence, trait.score),
            reverse=True,
        )[:4]
        answer = _general_answer(selected)

    evidence = _evidence_for_traits(selected, limit=4)
    confidence = _confidence(selected)
    return ProfileQuestionResponse(
        question=question,
        answer=answer,
        confidence=confidence,
        evidence_level=_answer_evidence_level(confidence, len(evidence)),
        evidence=evidence,
        suggested_followups=_followups_for_question(lowered),
        needs_more_evidence=profile.summary.get("needs_more_evidence", False),
    )


def correct_profile_observation(
    observation_id: str,
    payload: ProfileObservationUpdateRequest,
) -> PromptProfileResponse | None:
    if payload.summary is None and payload.score is None and payload.note is None:
        raise ValueError("Provide a summary, score, or note to correct the observation")

    with SessionLocal() as database:
        profile = ensure_local_profile(database)
        observation = database.scalar(
            select(TraitObservation).where(
                TraitObservation.id == observation_id,
                TraitObservation.profile_id == profile.id,
            )
        )
        if observation is None:
            return None

        override = _get_or_create_override(database, profile.id, observation.trait_key)
        override.action = "corrected"
        if payload.summary is not None:
            override.corrected_summary = payload.summary.strip()
        elif override.corrected_summary is None:
            override.corrected_summary = observation.summary
        if payload.score is not None:
            override.corrected_score = payload.score
        if payload.note is not None:
            override.note = payload.note.strip() or None
        override.updated_at = utc_now()
        profile.updated_at = utc_now()
        database.commit()

    return get_prompt_profile()


def delete_profile_observation(observation_id: str) -> ProfileObservationDeleteResponse | None:
    with SessionLocal() as database:
        profile = ensure_local_profile(database)
        observation = database.scalar(
            select(TraitObservation).where(
                TraitObservation.id == observation_id,
                TraitObservation.profile_id == profile.id,
            )
        )
        if observation is None:
            return None

        override = _get_or_create_override(database, profile.id, observation.trait_key)
        override.action = "hidden"
        override.corrected_summary = None
        override.corrected_score = None
        override.note = "Hidden by user"
        override.updated_at = utc_now()
        profile.updated_at = utc_now()
        trait_key = observation.trait_key
        database.commit()

    return ProfileObservationDeleteResponse(
        id=observation_id,
        deleted=True,
        trait_key=trait_key,
    )


def _get_or_create_override(
    database,
    profile_id: str,
    trait_key: str,
) -> ProfileObservationOverride:
    override = database.scalar(
        select(ProfileObservationOverride).where(
            ProfileObservationOverride.profile_id == profile_id,
            ProfileObservationOverride.trait_key == trait_key,
        )
    )
    if override is None:
        override = ProfileObservationOverride(profile_id=profile_id, trait_key=trait_key)
        database.add(override)
        database.flush()
    return override


def _missing_detail_items(
    traits: dict[str, TraitObservationResponse],
    profile: PromptProfileResponse,
) -> list[ProfileInsightItem]:
    if not traits:
        return [
            ProfileInsightItem(
                title="Add a few examples first",
                detail=(
                    "PromptPilot needs sessions or imports before it can identify "
                    "common missing details."
                ),
                confidence=0.15,
                action="Create a workspace session or import past chats.",
            )
        ]

    candidates: list[ProfileInsightItem] = []
    missing = traits.get("missing_context_patterns")
    context = traits.get("context_depth")
    constraints = traits.get("constraint_specificity")
    goal = traits.get("goal_clarity")
    sources = traits.get("source_expectation")

    if missing and missing.score >= 0.35:
        candidates.append(
            _item_from_trait(
                "Unresolved follow-up context",
                "Some prompts still leave required clarifying context open.",
                missing,
                "Answer or intentionally skip required follow-up questions before generating.",
            )
        )
    if context and context.score < 0.58:
        candidates.append(
            _item_from_trait(
                "Starting context",
                "Your initial prompts can benefit from a little more background.",
                context,
                "Add the situation, what you already tried, and the target outcome.",
            )
        )
    if constraints and constraints.score < 0.62:
        candidates.append(
            _item_from_trait(
                "Constraints and boundaries",
                "Constraints, tools, audience, or must-have requirements are not always explicit.",
                constraints,
                "Name the limits, tools, format, and success criteria up front.",
            )
        )
    if goal and goal.score < 0.65:
        candidates.append(
            _item_from_trait(
                "Concrete outcome",
                "The final deliverable can be stated more directly in some prompts.",
                goal,
                "Say exactly what the assistant should produce.",
            )
        )
    if sources and sources.score < 0.4 and profile.total_sessions:
        candidates.append(
            _item_from_trait(
                "Source expectations",
                "When accuracy matters, source or citation expectations are not always named.",
                sources,
                "Ask for official docs, citations, or evidence checks where relevant.",
            )
        )

    return candidates[:4] or [
        ProfileInsightItem(
            title="No strong missing-detail pattern yet",
            detail="The current evidence does not show one repeated omission.",
            confidence=_average_confidence(traits.values()),
            action="Keep refreshing the profile as more sessions build up.",
        )
    ]


def _preference_items(
    profile: PromptProfileResponse,
    sessions: list[ProblemSession],
    traits: dict[str, TraitObservationResponse],
) -> list[ProfileInsightItem]:
    items: list[ProfileInsightItem] = []
    for key, label in [
        ("tone", "Tone"),
        ("format", "Format"),
        ("detail_level", "Detail level"),
        ("formality", "Formality"),
        ("target_platform", "Target platform"),
    ]:
        common = _most_common_setting(sessions, key)
        if common:
            value, count = common
            items.append(
                ProfileInsightItem(
                    title=label,
                    detail=f"Most recent evidence leans toward {value.replace('_', ' ')}.",
                    confidence=min(0.95, 0.35 + (count * 0.12)),
                    evidence=[],
                    action=f"Use {value.replace('_', ' ')} as the default when it fits the task.",
                )
            )

    for trait_key in ["tone_preference", "format_preference", "formality_preference"]:
        trait = traits.get(trait_key)
        if trait and trait.confidence >= 0.45:
            items.append(
                _item_from_trait(
                    trait.trait_label,
                    trait.summary,
                    trait,
                    "Keep using the preference when the audience matches.",
                )
            )

    for preference in profile.platform_preferences[:2]:
        items.append(
            ProfileInsightItem(
                title=f"{preference.platform.title()} preference",
                detail=(
                    "Saved workspace settings show this platform has a reusable prompt style."
                ),
                confidence=preference.confidence,
                action="Start fresh sessions from this saved platform preference.",
            )
        )

    deduped: list[ProfileInsightItem] = []
    seen = set()
    for item in items:
        key = item.title.lower()
        if key not in seen:
            deduped.append(item)
            seen.add(key)
    return deduped[:6]


def _domain_items(sessions: list[ProblemSession]) -> list[ProfileInsightItem]:
    domain_counts = Counter(
        session.detected_domain
        for session in sessions
        if session.detected_domain
    )
    intent_counts = Counter(
        session.detected_intent
        for session in sessions
        if session.detected_intent
    )
    items = [
        ProfileInsightItem(
            title=domain.replace("_", " "),
            detail=f"{count} session{'s' if count != 1 else ''} in this domain.",
            confidence=min(0.95, 0.35 + count * 0.14),
            evidence=[],
            action="Use the confirmed domain field when it needs correction.",
        )
        for domain, count in domain_counts.most_common(4)
    ]
    items.extend(
        ProfileInsightItem(
            title=intent.replace("_", " "),
            detail=f"{count} task{'s' if count != 1 else ''} with this intent.",
            confidence=min(0.9, 0.32 + count * 0.12),
            action="Reuse successful prompt structures for recurring task types.",
        )
        for intent, count in intent_counts.most_common(2)
    )
    return items or [
        ProfileInsightItem(
            title="No frequent domains yet",
            detail="Domain patterns will appear after more workspace sessions are classified.",
            confidence=0.15,
            action="Run a few prompts through the workspace.",
        )
    ]


def _platform_items(
    profile: PromptProfileResponse,
    traits: dict[str, TraitObservationResponse],
) -> list[ProfileInsightItem]:
    items: list[ProfileInsightItem] = []
    technical = traits.get("technical_depth")
    constraints = traits.get("constraint_specificity")
    context = traits.get("context_depth")

    for preference in profile.platform_preferences[:3]:
        platform = preference.platform.replace("_", " ")
        items.append(
            ProfileInsightItem(
                title=f"Prompting for {platform.title()}",
                detail=(
                    "Saved settings suggest this platform should get explicit role, task, "
                    "context, constraints, output format, and verification instructions."
                ),
                confidence=preference.confidence,
                action="Keep platform-specific prompts explicit instead of relying on defaults.",
            )
        )

    if technical and technical.score >= 0.45:
        items.append(
            _item_from_trait(
                "Codex and coding assistants",
                "Your profile has enough technical signal to benefit from repo-aware prompts.",
                technical,
                "Mention files, constraints, verification commands, and expected code-change behavior.",
            )
        )
    if constraints and constraints.score < 0.65:
        items.append(
            _item_from_trait(
                "Platform guardrails",
                "Platform prompts will be stronger when constraints and boundaries are explicit.",
                constraints,
                "Add tools, allowed changes, test expectations, and non-goals.",
            )
        )
    if context and context.score < 0.58:
        items.append(
            _item_from_trait(
                "Context handoff",
                "Long-context assistants still need a clear handoff of the problem state.",
                context,
                "Summarize the current state before asking for analysis or code.",
            )
        )

    return items[:5] or [
        ProfileInsightItem(
            title="Platform advice is forming",
            detail="Choose target platforms in the workspace to build stronger platform advice.",
            confidence=0.2,
            action="Try Codex, ChatGPT, Claude, Gemini, or Cursor on a few sessions.",
        )
    ]


def _revision_items(revisions: list[PromptRevision]) -> list[ProfileInsightItem]:
    return [
        ProfileInsightItem(
            title=revision.revision_type.replace("_", " ").title(),
            detail=revision.rationale or "Prompt was refined from the workspace flow.",
            confidence=0.7,
            evidence=[
                ProfileEvidenceReference(
                    type="revision",
                    label="Prompt revision",
                    excerpt=_excerpt(revision.after_text, 180),
                    session_id=revision.session_id,
                )
            ],
            action="Review recent revisions to see which details changed the prompt.",
        )
        for revision in revisions
    ]


def _missing_answer(
    traits: list[TraitObservationResponse],
    items: list[ProfileInsightItem],
) -> str:
    if items:
        top = items[0]
        return (
            f"The clearest pattern is {top.title.lower()}. {top.detail} "
            f"Best next move: {top.action}"
        )
    return _general_answer(traits)


def _codex_answer(
    traits: list[TraitObservationResponse],
    items: list[ProfileInsightItem],
) -> str:
    if items:
        top = items[0]
        return (
            f"For Codex-style work, your prompt should make repo context and verification "
            f"concrete. {top.detail} {top.action}"
        )
    return (
        "For Codex, include the files or modules involved, the desired behavior, constraints, "
        "test commands, and what kind of code change you expect."
    )


def _preference_answer(
    traits: list[TraitObservationResponse],
    items: list[ProfileInsightItem],
) -> str:
    if items:
        details = " ".join(f"{item.title}: {item.detail}" for item in items[:3])
        return f"Your strongest visible preferences are: {details}"
    return _general_answer(traits)


def _domain_answer(
    traits: list[TraitObservationResponse],
    items: list[ProfileInsightItem],
) -> str:
    if items:
        details = "; ".join(f"{item.title} ({item.detail})" for item in items[:4])
        return f"Your most visible domains and task types are: {details}"
    return _general_answer(traits)


def _research_answer(traits: list[TraitObservationResponse]) -> str:
    source = next((trait for trait in traits if trait.trait_key == "source_expectation"), None)
    if source and source.score < 0.55:
        return (
            "For research prompts, the biggest upgrade is to state source expectations. "
            "Ask for source type, recency, citation style, comparison criteria, and what "
            "should happen when evidence is weak."
        )
    return (
        "Your research prompts should keep the question, scope, evidence standard, "
        "source type, and output format explicit. That gives the assistant a cleaner "
        "target and makes weak evidence easier to spot."
    )


def _general_answer(traits: list[TraitObservationResponse]) -> str:
    if not traits:
        return "The profile is still forming, so I need more examples before naming a pattern."
    strongest = sorted(traits, key=lambda trait: (trait.confidence, trait.score), reverse=True)[0]
    return (
        f"The strongest available signal is {strongest.trait_label.lower()}. "
        f"{strongest.summary} Use that as a starting point, but treat it as "
        "tentative if the evidence level is still low."
    )


def _item_from_trait(
    title: str,
    detail: str,
    trait: TraitObservationResponse,
    action: str,
) -> ProfileInsightItem:
    return ProfileInsightItem(
        title=title,
        detail=detail,
        confidence=trait.confidence,
        evidence=_refs_for_trait(trait, limit=2),
        action=action,
    )


def _refs_for_trait(
    trait: TraitObservationResponse,
    limit: int,
) -> list[ProfileEvidenceReference]:
    refs = []
    for item in trait.evidence[:limit]:
        refs.append(
            ProfileEvidenceReference(
                type=str(item.get("type") or "trait"),
                label=trait.trait_label,
                excerpt=item.get("excerpt"),
                session_id=item.get("session_id"),
                imported_message_id=item.get("imported_message_id"),
                trait_key=trait.trait_key,
                confidence=trait.confidence,
            )
        )
    if not refs:
        for signal in trait.signals[:limit]:
            refs.append(
                ProfileEvidenceReference(
                    type=signal.source_type,
                    label=signal.signal_label,
                    excerpt=signal.evidence.get("excerpt"),
                    session_id=signal.evidence.get("session_id"),
                    imported_message_id=signal.evidence.get("imported_message_id"),
                    trait_key=trait.trait_key,
                    confidence=signal.confidence,
                )
            )
    return refs


def _evidence_for_traits(
    traits: list[TraitObservationResponse],
    limit: int,
) -> list[ProfileEvidenceReference]:
    evidence: list[ProfileEvidenceReference] = []
    for trait in traits:
        evidence.extend(_refs_for_trait(trait, limit=2))
    return evidence[:limit]


def _select_traits(
    traits: dict[str, TraitObservationResponse],
    keys: list[str],
) -> list[TraitObservationResponse]:
    return [traits[key] for key in keys if key in traits]


def _matches(text: str, terms: set[str]) -> bool:
    return any(term in text for term in terms)


def _confidence(traits: list[TraitObservationResponse]) -> float:
    if not traits:
        return 0.15
    return round(mean(trait.confidence for trait in traits), 2)


def _average_confidence(traits) -> float:
    values = [trait.confidence for trait in traits]
    return round(mean(values), 2) if values else 0.15


def _answer_evidence_level(confidence: float, evidence_count: int) -> str:
    if evidence_count == 0:
        return "none"
    if confidence < 0.45:
        return "tentative"
    if confidence < 0.72:
        return "emerging"
    return "strong"


def _followups_for_question(question: str) -> list[str]:
    if _matches(question, {"codex", "code", "repo"}):
        return [
            "What should I include before asking Codex to edit code?",
            "Which constraints should my coding prompts name?",
            "How can I make verification clearer?",
        ]
    if _matches(question, {"tone", "format", "prefer"}):
        return [
            "What format do I usually prefer?",
            "How formal should my prompts be?",
            "What detail level fits my profile?",
        ]
    if _matches(question, {"domain", "topic", "task"}):
        return [
            "Which task types show up most?",
            "Where does domain detection need correction?",
            "How should I prompt in my frequent domains?",
        ]
    return SUGGESTED_QUESTIONS[:3]


def _most_common_setting(
    sessions: list[ProblemSession],
    key: str,
) -> tuple[str, int] | None:
    counts = Counter(
        str(session.user_settings.get(key))
        for session in sessions
        if isinstance(session.user_settings, dict) and session.user_settings.get(key)
    )
    return counts.most_common(1)[0] if counts else None


def _excerpt(text: str, limit: int) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 3]}..."
