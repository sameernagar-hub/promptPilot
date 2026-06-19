from collections import Counter, defaultdict
from dataclasses import dataclass
from statistics import mean
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload

from app.db import SessionLocal, store
from app.models import (
    ConversationImport,
    ImportedConversation,
    ImportedMessage,
    PlatformPreference,
    ProfileObservationOverride,
    ProblemSession,
    PromptingTrait,
    PromptingTraitSignal,
    TraitObservation,
    UserPromptProfile,
    utc_now,
)
from app.schemas import (
    PlatformPreferenceResponse,
    PromptingTraitSignalResponse,
    PromptProfileResponse,
    TraitObservationResponse,
)


LOCAL_PROFILE_KEY = "local"
PROFILE_ANALYZER_VERSION = "trait_detector_v1"
LEGACY_ANALYZER_VERSION = "session_summary_v1"

TRAIT_DEFINITIONS = [
    {
        "trait_key": "context_depth",
        "label": "Context depth",
        "description": "How much starting context the user tends to include.",
        "category": "input_quality",
        "scoring_direction": "higher_means_more_context",
    },
    {
        "trait_key": "goal_clarity",
        "label": "Goal clarity",
        "description": "How often the prompt states a concrete desired outcome.",
        "category": "input_quality",
        "scoring_direction": "higher_means_clearer_goal",
    },
    {
        "trait_key": "constraint_specificity",
        "label": "Constraint specificity",
        "description": "How often constraints, boundaries, tools, or requirements appear.",
        "category": "input_quality",
        "scoring_direction": "higher_means_more_constraints",
    },
    {
        "trait_key": "domain_precision",
        "label": "Domain precision",
        "description": "How confidently PromptPilot can infer the user's domain.",
        "category": "domain",
        "scoring_direction": "higher_means_more_precise_domain",
    },
    {
        "trait_key": "format_preference",
        "label": "Format preference",
        "description": "Whether the user shows a consistent output format preference.",
        "category": "preferences",
        "scoring_direction": "higher_means_stronger_preference",
    },
    {
        "trait_key": "tone_preference",
        "label": "Tone preference",
        "description": "Whether the user shows a consistent tone preference.",
        "category": "preferences",
        "scoring_direction": "higher_means_stronger_preference",
    },
    {
        "trait_key": "formality_preference",
        "label": "Formality preference",
        "description": "Whether the user signals casual, neutral, or formal communication needs.",
        "category": "preferences",
        "scoring_direction": "higher_means_more_evidence",
    },
    {
        "trait_key": "iteration_style",
        "label": "Iteration style",
        "description": "How often the user answers follow-up questions in the workflow.",
        "category": "workflow",
        "scoring_direction": "higher_means_more_iterative",
    },
    {
        "trait_key": "risk_awareness",
        "label": "Risk awareness",
        "description": "How often safety posture appears in risky or sensitive prompts.",
        "category": "safety",
        "scoring_direction": "higher_means_more_safety_signal",
    },
    {
        "trait_key": "source_expectation",
        "label": "Source expectation",
        "description": "How often the user asks for web or official-document grounding.",
        "category": "preferences",
        "scoring_direction": "higher_means_more_source_grounding",
    },
    {
        "trait_key": "technical_depth",
        "label": "Technical depth",
        "description": "How often the prompt includes technical tools, stacks, or expert settings.",
        "category": "domain",
        "scoring_direction": "higher_means_more_technical",
    },
    {
        "trait_key": "missing_context_patterns",
        "label": "Missing context patterns",
        "description": "How often generated clarifying questions remain unanswered.",
        "category": "input_quality",
        "scoring_direction": "higher_means_more_missing_context",
    },
]

GOAL_TERMS = {
    "build",
    "choose",
    "compare",
    "create",
    "draft",
    "explain",
    "fix",
    "help",
    "implement",
    "learn",
    "make",
    "need",
    "plan",
    "research",
    "want",
    "write",
}

CONSTRAINT_TERMS = {
    "avoid",
    "budget",
    "deadline",
    "for",
    "must",
    "only",
    "should",
    "using",
    "without",
    "with",
}

FORMAT_TERMS = {
    "checklist": {"checklist", "steps", "todo"},
    "guide": {"guide", "walkthrough"},
    "table": {"table", "matrix"},
    "conversation": {"conversation", "dialogue", "coach"},
    "plan": {"plan", "roadmap", "phases"},
}

TONE_TERMS = {
    "direct": {"direct", "blunt", "straightforward"},
    "friendly": {"friendly", "warm", "kind"},
    "technical": {"technical", "expert", "precise"},
}

FORMALITY_TERMS = {
    "formal": {"formal", "professional", "respectful", "polished"},
    "casual": {"casual", "informal", "simple"},
    "neutral": {"neutral", "balanced"},
}

RISK_TERMS = {
    "danger",
    "financial",
    "legal",
    "medical",
    "risk",
    "safe",
    "safety",
    "secure",
}

SOURCE_TERMS = {
    "cite",
    "evidence",
    "official",
    "reference",
    "research",
    "source",
    "sources",
}

TECHNICAL_TERMS = {
    "api",
    "app",
    "bug",
    "code",
    "database",
    "deploy",
    "fastapi",
    "next",
    "python",
    "react",
    "repo",
    "typescript",
}


@dataclass(frozen=True)
class NormalizedExample:
    source_type: str
    source_ref: str
    text: str
    settings: dict[str, Any]
    domain: str | None = None
    intent: str | None = None
    risk_level: str | None = None
    classification_confidence: float = 0.0
    answered_questions: int = 0
    total_questions: int = 0
    unanswered_required: int = 0
    session_id: str | None = None
    imported_message_id: str | None = None


@dataclass(frozen=True)
class SignalDraft:
    trait_key: str
    signal_key: str
    signal_label: str
    score: float
    weight: float
    confidence: float
    explanation: str
    evidence: dict[str, Any]
    source_type: str
    source_ref: str
    session_id: str | None = None
    imported_message_id: str | None = None


def get_prompt_profile() -> PromptProfileResponse:
    with SessionLocal() as database:
        profile = _ensure_profile(database)
        _ensure_traits(database)
        database.commit()
        if profile.last_refreshed_at is None:
            return refresh_prompt_profile()
        return _profile_response(database, profile.id)


def refresh_prompt_profile() -> PromptProfileResponse:
    with SessionLocal() as database:
        profile = _ensure_profile(database)
        traits = _ensure_traits(database)
        database.flush()

        sessions = list(
            database.scalars(
                select(ProblemSession)
                .options(selectinload(ProblemSession.question_rows))
                .order_by(ProblemSession.created_at)
            )
        )
        imported_messages = list(
            database.scalars(
                select(ImportedMessage)
                .options(
                    selectinload(ImportedMessage.conversation)
                    .selectinload(ImportedConversation.conversation_import)
                )
                .where(ImportedMessage.role.in_(["user", "human"]))
                .order_by(ImportedMessage.created_at)
            )
        )
        total_imports = database.scalar(select(func.count(ConversationImport.id))) or 0

        database.execute(
            delete(TraitObservation).where(
                TraitObservation.profile_id == profile.id,
                TraitObservation.source_type.in_(
                    [PROFILE_ANALYZER_VERSION, LEGACY_ANALYZER_VERSION]
                ),
            )
        )
        database.execute(
            delete(PromptingTraitSignal).where(
                PromptingTraitSignal.profile_id == profile.id,
                PromptingTraitSignal.source_type == PROFILE_ANALYZER_VERSION,
            )
        )

        examples = _normalize_examples(sessions, imported_messages)
        signal_drafts = _extract_signals(examples)
        signals = [
            _signal(profile.id, traits, draft)
            for draft in signal_drafts
        ]
        observations = _build_observations(profile.id, traits, examples, signals)

        for signal in signals:
            database.add(signal)
        for observation in observations:
            database.add(observation)

        profile.total_sessions = len(sessions)
        profile.total_imports = int(total_imports)
        profile.observation_count = len(observations)
        profile.status = _profile_status(len(examples), len(observations))
        profile.summary = _profile_summary(examples, observations, signals, int(total_imports))
        profile.last_refreshed_at = utc_now()
        profile.updated_at = utc_now()

        database.commit()
        return _profile_response(database, profile.id)


def reset_prompt_profile_data() -> dict[str, int]:
    with SessionLocal() as database:
        profile = _ensure_profile(database)
        counts = {
            "observation_overrides": _deleted_count(
                database.execute(
                    delete(ProfileObservationOverride).where(
                        ProfileObservationOverride.profile_id == profile.id
                    )
                )
            ),
            "trait_observations": _deleted_count(
                database.execute(
                    delete(TraitObservation).where(TraitObservation.profile_id == profile.id)
                )
            ),
            "trait_signals": _deleted_count(
                database.execute(
                    delete(PromptingTraitSignal).where(
                        PromptingTraitSignal.profile_id == profile.id
                    )
                )
            ),
            "platform_preferences": _deleted_count(
                database.execute(
                    delete(PlatformPreference).where(PlatformPreference.profile_id == profile.id)
                )
            ),
        }
        profile.status = "empty"
        reset_at = utc_now()
        profile.summary = {"needs_more_evidence": True, "reset_at": reset_at.isoformat()}
        profile.observation_count = 0
        profile.last_refreshed_at = reset_at
        profile.updated_at = reset_at
        database.commit()

    store.record_audit_log(
        event_type="profile_data_deleted",
        entity_type="user_prompt_profile",
        entity_id=LOCAL_PROFILE_KEY,
        metadata={"deleted_counts": counts},
    )
    return counts


def ensure_local_profile(database) -> UserPromptProfile:
    return _ensure_profile(database)


def _ensure_profile(database) -> UserPromptProfile:
    profile = database.scalar(
        select(UserPromptProfile).where(UserPromptProfile.profile_key == LOCAL_PROFILE_KEY)
    )
    if profile is None:
        profile = UserPromptProfile(profile_key=LOCAL_PROFILE_KEY, display_name="Local profile")
        database.add(profile)
        database.flush()
    return profile


def _deleted_count(result) -> int:
    count = getattr(result, "rowcount", 0)
    return count if isinstance(count, int) and count > 0 else 0


def _ensure_traits(database) -> dict[str, PromptingTrait]:
    existing = {
        trait.trait_key: trait
        for trait in database.scalars(select(PromptingTrait))
    }
    for definition in TRAIT_DEFINITIONS:
        trait = existing.get(definition["trait_key"])
        if trait is None:
            trait = PromptingTrait(**definition)
            database.add(trait)
            existing[trait.trait_key] = trait
        else:
            trait.label = definition["label"]
            trait.description = definition["description"]
            trait.category = definition["category"]
            trait.scoring_direction = definition["scoring_direction"]
    database.flush()
    return existing


def _normalize_examples(
    sessions: list[ProblemSession],
    imported_messages: list[ImportedMessage],
) -> list[NormalizedExample]:
    examples: list[NormalizedExample] = []
    for session in sessions:
        classification = session.classification or {}
        examples.append(
            NormalizedExample(
                source_type="session",
                source_ref=session.id,
                text=session.raw_input,
                settings=session.user_settings or {},
                domain=session.detected_domain,
                intent=session.detected_intent,
                risk_level=session.risk_level,
                classification_confidence=float(classification.get("confidence", 0.0)),
                answered_questions=len(session.answers),
                total_questions=len(session.question_rows),
                unanswered_required=sum(
                    1 for question in session.question_rows if question.required and not question.answer
                ),
                session_id=session.id,
            )
        )

    for message in imported_messages:
        conversation = message.conversation
        conversation_import = conversation.conversation_import if conversation else None
        platform = conversation_import.platform if conversation_import else "manual"
        examples.append(
            NormalizedExample(
                source_type="imported_message",
                source_ref=message.id,
                text=message.redacted_text or message.message_text,
                settings={"platform": platform},
                imported_message_id=message.id,
            )
        )

    return examples


def _extract_signals(examples: list[NormalizedExample]) -> list[SignalDraft]:
    signals: list[SignalDraft] = []
    for example in examples:
        signals.extend(_signals_for_example(example))
    return signals


def _signals_for_example(example: NormalizedExample) -> list[SignalDraft]:
    text = example.text
    lowered = text.lower()
    words = _word_count(text)
    signals = [
        _draft(
            example,
            "context_depth",
            "word_count",
            "Starting context length",
            _clamp(words / 70),
            1.0,
            0.76,
            f"Example contains {words} words of starting context.",
        ),
        _draft(
            example,
            "goal_clarity",
            "outcome_terms",
            "Outcome terms",
            1.0 if _contains_any(lowered, GOAL_TERMS) else 0.2,
            1.0,
            0.72,
            "The request includes an action or outcome signal."
            if _contains_any(lowered, GOAL_TERMS)
            else "The request has limited explicit outcome language.",
        ),
        _draft(
            example,
            "constraint_specificity",
            "constraint_terms",
            "Constraint terms",
            _clamp((_term_count(lowered, CONSTRAINT_TERMS) + example.answered_questions) / 4),
            1.0,
            0.68,
            "Constraints are inferred from requirement terms and answered follow-up questions.",
        ),
        _draft(
            example,
            "domain_precision",
            "classification_confidence",
            "Domain confidence",
            _domain_score(example),
            1.0,
            0.7,
            _domain_explanation(example),
        ),
        _draft(
            example,
            "iteration_style",
            "answered_questions",
            "Follow-up participation",
            _question_answer_score(example),
            1.0,
            0.68,
            f"{example.answered_questions} of {example.total_questions} clarifying questions are answered.",
        ),
        _draft(
            example,
            "risk_awareness",
            "risk_terms",
            "Safety and risk signal",
            _risk_signal_score(example, lowered),
            1.0,
            0.66,
            "Risk signal uses risk level, safe-only settings, and safety language.",
        ),
        _draft(
            example,
            "source_expectation",
            "source_terms",
            "Source expectation",
            _source_signal_score(example, lowered),
            1.0,
            0.7,
            "Source expectation uses source settings and citation/evidence language.",
        ),
        _draft(
            example,
            "technical_depth",
            "technical_terms",
            "Technical specificity",
            _technical_signal_score(example, lowered),
            1.0,
            0.7,
            "Technical depth uses tool, code, stack, and expert-skill signals.",
        ),
        _draft(
            example,
            "missing_context_patterns",
            "unanswered_required",
            "Unanswered required context",
            _missing_context_score(example, words),
            1.0,
            0.7,
            "Missing context uses unanswered required questions and very short prompts.",
        ),
    ]

    format_signal = _preference_signal(example, lowered, "format", FORMAT_TERMS)
    if format_signal:
        signals.append(format_signal)
    tone_signal = _preference_signal(example, lowered, "tone", TONE_TERMS)
    if tone_signal:
        signals.append(tone_signal)
    formality_signal = _preference_signal(example, lowered, "formality", FORMALITY_TERMS)
    if formality_signal:
        signals.append(formality_signal)
    return signals


def _draft(
    example: NormalizedExample,
    trait_key: str,
    signal_key: str,
    signal_label: str,
    score: float,
    weight: float,
    confidence: float,
    explanation: str,
) -> SignalDraft:
    return SignalDraft(
        trait_key=trait_key,
        signal_key=signal_key,
        signal_label=signal_label,
        score=round(_clamp(score), 2),
        weight=weight,
        confidence=round(_clamp(confidence), 2),
        explanation=explanation,
        evidence=_example_evidence(example),
        source_type=PROFILE_ANALYZER_VERSION,
        source_ref=example.source_ref,
        session_id=example.session_id,
        imported_message_id=example.imported_message_id,
    )


def _preference_signal(
    example: NormalizedExample,
    lowered: str,
    preference_key: str,
    term_map: dict[str, set[str]],
) -> SignalDraft | None:
    trait_key = f"{preference_key}_preference"
    setting_value = example.settings.get(preference_key)
    if isinstance(setting_value, str) and setting_value in term_map:
        return _draft(
            example,
            trait_key,
            f"selected_{preference_key}_{setting_value}",
            f"Selected {preference_key}",
            1.0,
            1.0,
            0.78,
            f"The active settings select {setting_value.replace('_', ' ')} {preference_key}.",
        )

    detected = [
        value for value, terms in term_map.items()
        if _contains_any(lowered, terms)
    ]
    if not detected:
        return None
    value = detected[0]
    return _draft(
        example,
        trait_key,
        f"mentioned_{preference_key}_{value}",
        f"Mentioned {preference_key}",
        0.86,
        0.8,
        0.64,
        f"The text mentions {value.replace('_', ' ')} {preference_key} language.",
    )


def _signal(
    profile_id: str,
    traits: dict[str, PromptingTrait],
    draft: SignalDraft,
) -> PromptingTraitSignal:
    trait = traits.get(draft.trait_key)
    return PromptingTraitSignal(
        profile_id=profile_id,
        trait_id=trait.id if trait else None,
        trait_key=draft.trait_key,
        signal_key=draft.signal_key,
        signal_label=draft.signal_label,
        score=draft.score,
        weight=draft.weight,
        confidence=draft.confidence,
        explanation=draft.explanation,
        evidence=draft.evidence,
        source_type=draft.source_type,
        source_ref=draft.source_ref,
        session_id=draft.session_id,
        imported_message_id=draft.imported_message_id,
    )


def _build_observations(
    profile_id: str,
    traits: dict[str, PromptingTrait],
    examples: list[NormalizedExample],
    signals: list[PromptingTraitSignal],
) -> list[TraitObservation]:
    grouped: dict[str, list[PromptingTraitSignal]] = defaultdict(list)
    for signal in signals:
        grouped[signal.trait_key].append(signal)

    observations: list[TraitObservation] = []
    for definition in TRAIT_DEFINITIONS:
        trait_key = definition["trait_key"]
        trait = traits[trait_key]
        trait_signals = grouped.get(trait_key, [])
        score = _weighted_average(trait_signals)
        confidence = _observation_confidence(examples, trait_signals)
        evidence = _observation_evidence(trait_signals)
        observations.append(
            TraitObservation(
                profile_id=profile_id,
                trait_id=trait.id,
                trait_key=trait_key,
                score=round(score, 2),
                confidence=round(confidence, 2),
                summary=_observation_summary(definition, trait_signals, score, confidence),
                evidence=evidence,
                source_type=PROFILE_ANALYZER_VERSION,
                source_ref="local_examples",
            )
        )
    return observations


def _profile_response(database, profile_id: str) -> PromptProfileResponse:
    profile = database.scalar(
        select(UserPromptProfile)
        .options(
            selectinload(UserPromptProfile.observations).selectinload(
                TraitObservation.trait
            ),
            selectinload(UserPromptProfile.signals).selectinload(
                PromptingTraitSignal.trait
            ),
            selectinload(UserPromptProfile.platform_preferences),
            selectinload(UserPromptProfile.observation_overrides),
        )
        .where(UserPromptProfile.id == profile_id)
    )
    if profile is None:
        raise ValueError(f"Profile not found: {profile_id}")

    signals_by_trait: dict[str, list[PromptingTraitSignal]] = defaultdict(list)
    for signal in profile.signals:
        signals_by_trait[signal.trait_key].append(signal)

    overrides = {
        override.trait_key: override
        for override in profile.observation_overrides
    }
    traits = [
        TraitObservationResponse(
            id=observation.id,
            trait_key=observation.trait_key,
            trait_label=observation.trait.label if observation.trait else observation.trait_key,
            category=observation.trait.category if observation.trait else "foundation",
            score=(
                overrides[observation.trait_key].corrected_score
                if observation.trait_key in overrides
                and overrides[observation.trait_key].corrected_score is not None
                else observation.score
            ),
            confidence=observation.confidence,
            evidence_level=_evidence_level(observation.confidence, len(signals_by_trait[observation.trait_key])),
            signal_count=len(signals_by_trait[observation.trait_key]),
            summary=(
                overrides[observation.trait_key].corrected_summary
                if observation.trait_key in overrides
                and overrides[observation.trait_key].corrected_summary
                else observation.summary
            ),
            evidence=observation.evidence,
            signals=[
                PromptingTraitSignalResponse(
                    id=signal.id,
                    trait_key=signal.trait_key,
                    signal_key=signal.signal_key,
                    signal_label=signal.signal_label,
                    score=signal.score,
                    weight=signal.weight,
                    confidence=signal.confidence,
                    explanation=signal.explanation,
                    evidence=signal.evidence,
                    source_type=signal.source_type,
                    source_ref=signal.source_ref,
                    created_at=signal.created_at,
                )
                for signal in _representative_signals(
                    signals_by_trait[observation.trait_key],
                    limit=3,
                )
            ],
            source_type=observation.source_type,
            source_ref=observation.source_ref,
            user_corrected=observation.trait_key in overrides
            and overrides[observation.trait_key].action == "corrected",
            user_note=(
                overrides[observation.trait_key].note
                if observation.trait_key in overrides
                else None
            ),
            created_at=observation.created_at,
            updated_at=observation.updated_at,
        )
        for observation in profile.observations
        if overrides.get(observation.trait_key) is None
        or overrides[observation.trait_key].action != "hidden"
    ]
    traits.sort(key=lambda item: (item.category, item.trait_label))

    return PromptProfileResponse(
        id=profile.id,
        profile_key=profile.profile_key,
        display_name=profile.display_name,
        status=profile.status,
        summary=profile.summary,
        total_sessions=profile.total_sessions,
        total_imports=profile.total_imports,
        observation_count=profile.observation_count,
        last_refreshed_at=profile.last_refreshed_at,
        traits=traits,
        platform_preferences=[
            PlatformPreferenceResponse.model_validate(preference)
            for preference in sorted(
                profile.platform_preferences,
                key=lambda item: (item.confidence, item.updated_at),
                reverse=True,
            )
        ],
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def _profile_status(example_count: int, observation_count: int) -> str:
    if example_count == 0:
        return "empty"
    if observation_count < len(TRAIT_DEFINITIONS) or example_count < 3:
        return "partial"
    return "populated"


def _profile_summary(
    examples: list[NormalizedExample],
    observations: list[TraitObservation],
    signals: list[PromptingTraitSignal],
    import_count: int,
) -> dict[str, Any]:
    if not examples:
        return {
            "headline": "No prompting evidence yet",
            "session_count": 0,
            "import_count": import_count,
            "signal_count": 0,
            "strongest_traits": [],
            "tentative_traits": [],
            "needs_more_evidence": True,
        }

    strongest = sorted(
        observations,
        key=lambda observation: (observation.score, observation.confidence),
        reverse=True,
    )[:3]
    tentative = [
        observation.trait_key
        for observation in observations
        if _evidence_level(
            observation.confidence,
            sum(1 for signal in signals if signal.trait_key == observation.trait_key),
        )
        in {"none", "tentative"}
    ]
    session_count = sum(1 for example in examples if example.source_type == "session")
    imported_count = sum(1 for example in examples if example.source_type == "imported_message")
    return {
        "headline": f"Profile is based on {len(examples)} prompting examples",
        "session_count": session_count,
        "import_count": import_count,
        "imported_message_count": imported_count,
        "signal_count": len(signals),
        "strongest_traits": [
            {
                "trait_key": observation.trait_key,
                "score": observation.score,
                "confidence": observation.confidence,
            }
            for observation in strongest
        ],
        "tentative_traits": tentative,
        "needs_more_evidence": len(examples) < 3,
    }


def _observation_summary(
    definition: dict[str, str],
    signals: list[PromptingTraitSignal],
    score: float,
    confidence: float,
) -> str:
    if not signals:
        return f"There is not enough evidence yet to assess {definition['label'].lower()}."

    signal_count = len(signals)
    strongest = _representative_signals(signals, limit=1)[0]
    level = _evidence_level(confidence, signal_count)
    return (
        f"{definition['label']} is {level} with a {round(score * 100)} score from "
        f"{signal_count} signals. Strongest signal: {strongest.signal_label.lower()}."
    )


def _representative_signals(
    signals: list[PromptingTraitSignal],
    limit: int,
) -> list[PromptingTraitSignal]:
    return sorted(
        signals,
        key=lambda signal: (signal.confidence * signal.weight, signal.score),
        reverse=True,
    )[:limit]


def _observation_evidence(signals: list[PromptingTraitSignal]) -> list[dict[str, Any]]:
    return [
        signal.evidence
        for signal in _representative_signals(signals, limit=3)
        if signal.evidence
    ]


def _weighted_average(signals: list[PromptingTraitSignal]) -> float:
    if not signals:
        return 0.0
    total_weight = sum(signal.weight for signal in signals)
    if total_weight == 0:
        return 0.0
    return _clamp(sum(signal.score * signal.weight for signal in signals) / total_weight)


def _observation_confidence(
    examples: list[NormalizedExample],
    signals: list[PromptingTraitSignal],
) -> float:
    if not signals:
        return 0.15
    source_count = len({signal.source_ref for signal in signals if signal.source_ref})
    source_type_count = len({signal.source_type for signal in signals})
    mean_signal_confidence = mean(signal.confidence for signal in signals)
    evidence_volume = min(source_count, 8) * 0.055
    signal_volume = min(len(signals), 24) * 0.012
    source_diversity = 0.05 if source_type_count > 1 else 0.0
    low_evidence_penalty = 0.12 if len(examples) < 3 else 0.0
    return _clamp(
        0.22
        + evidence_volume
        + signal_volume
        + source_diversity
        + (mean_signal_confidence * 0.35)
        - low_evidence_penalty
    )


def _evidence_level(confidence: float, signal_count: int) -> str:
    if signal_count == 0:
        return "none"
    if confidence < 0.45 or signal_count < 3:
        return "tentative"
    if confidence < 0.72 or signal_count < 8:
        return "emerging"
    return "strong"


def _example_evidence(example: NormalizedExample) -> dict[str, Any]:
    return {
        "type": example.source_type,
        "session_id": example.session_id,
        "imported_message_id": example.imported_message_id,
        "excerpt": _excerpt(example.text),
        "domain": example.domain,
        "intent": example.intent,
        "risk_level": example.risk_level,
        "source_ref": example.source_ref,
    }


def _word_count(text: str) -> int:
    return len([word for word in text.split() if word.strip()])


def _contains_any(text: str, terms: set[str]) -> bool:
    return any(term in text for term in terms)


def _term_count(text: str, terms: set[str]) -> int:
    return sum(1 for term in terms if term in text)


def _domain_score(example: NormalizedExample) -> float:
    if example.source_type != "session":
        return 0.0
    if not example.domain or example.domain == "general_problem_solving":
        return min(example.classification_confidence, 0.35)
    return _clamp(0.4 + (example.classification_confidence * 0.6))


def _domain_explanation(example: NormalizedExample) -> str:
    if not example.domain:
        return "No domain has been detected for this example yet."
    return (
        f"Detected domain is {example.domain.replace('_', ' ')} "
        f"with {round(example.classification_confidence * 100)} confidence."
    )


def _question_answer_score(example: NormalizedExample) -> float:
    if example.total_questions == 0:
        return 0.0
    return _clamp(example.answered_questions / example.total_questions)


def _risk_signal_score(example: NormalizedExample, lowered: str) -> float:
    risk_level_score = 1.0 if example.risk_level in {"medium", "high"} else 0.0
    setting_score = 1.0 if example.settings.get("risk") == "safe_only" else 0.0
    text_score = min(_term_count(lowered, RISK_TERMS) / 2, 1.0)
    return _clamp(max(risk_level_score, setting_score, text_score))


def _source_signal_score(example: NormalizedExample, lowered: str) -> float:
    setting_score = 1.0 if example.settings.get("sources", "none") != "none" else 0.0
    text_score = min(_term_count(lowered, SOURCE_TERMS) / 2, 1.0)
    return _clamp(max(setting_score, text_score))


def _technical_signal_score(example: NormalizedExample, lowered: str) -> float:
    term_score = min(_term_count(lowered, TECHNICAL_TERMS) / 4, 1.0)
    setting_score = 0.4 if example.settings.get("skill_level") == "expert" else 0.0
    return _clamp(term_score + setting_score)


def _missing_context_score(example: NormalizedExample, word_count: int) -> float:
    if example.total_questions > 0:
        return _clamp(example.unanswered_required / max(example.total_questions, 1))
    return 0.7 if word_count < 8 else 0.0


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _excerpt(text: str, limit: int = 140) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 3]}..."
