import json
from statistics import mean
from typing import Any

from sqlalchemy import select
from app.config import get_settings
from app.db import SessionLocal, store
from app.models import (
    ConversationImport,
    PromptIntelligenceReport,
)
from app.schemas import (
    ConversationImportRequest,
    ConversationImportResponse,
    ImportedMessageResponse,
    ProfileEvidenceReference,
    PromptBehaviorPattern,
    PromptIntelligenceAnalyzeRequest,
    PromptIntelligenceComparison,
    PromptIntelligenceRecommendation,
    PromptIntelligenceReportResponse,
    PromptIntelligenceScore,
)
from app.services.import_service import (
    create_conversation_import,
    get_conversation_import,
)
from app.services.profile_analyzer import ensure_local_profile, get_prompt_profile
from app.services.profile_insights import get_profile_insights


REPORT_VERSION = "prompt_intelligence_v1"
LOCAL_MODEL = "local-prompt-intelligence-v1"
MAX_MODEL_TRANSCRIPT_CHARS = 18_000

ACTION_TERMS = {
    "analyze",
    "build",
    "compare",
    "create",
    "draft",
    "explain",
    "fix",
    "help",
    "implement",
    "improve",
    "plan",
    "review",
    "write",
}
CONSTRAINT_TERMS = {
    "avoid",
    "because",
    "deadline",
    "do not",
    "must",
    "only",
    "should",
    "unless",
    "using",
    "without",
}
EVIDENCE_TERMS = {
    "cite",
    "evidence",
    "official",
    "reference",
    "source",
    "sources",
    "verify",
}
TECHNICAL_TERMS = {
    "api",
    "backend",
    "build",
    "code",
    "codex",
    "database",
    "deploy",
    "env",
    "frontend",
    "github",
    "openai",
    "python",
    "react",
    "repo",
    "typescript",
}

OPENAI_REPORT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "headline",
        "summary",
        "style_scores",
        "behavior_patterns",
        "recommendations",
        "next_prompt_recipe",
        "comparisons",
    ],
    "properties": {
        "headline": {"type": "string"},
        "summary": {"type": "string"},
        "style_scores": {
            "type": "array",
            "minItems": 6,
            "maxItems": 6,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "key",
                    "label",
                    "score",
                    "verdict",
                    "explanation",
                    "improvement",
                    "evidence",
                ],
                "properties": {
                    "key": {"type": "string"},
                    "label": {"type": "string"},
                    "score": {"type": "integer", "minimum": 0, "maximum": 100},
                    "verdict": {"type": "string"},
                    "explanation": {"type": "string"},
                    "improvement": {"type": "string"},
                    "evidence": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            },
        },
        "behavior_patterns": {
            "type": "array",
            "minItems": 3,
            "maxItems": 5,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["title", "detail", "confidence", "evidence"],
                "properties": {
                    "title": {"type": "string"},
                    "detail": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "evidence": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "recommendations": {
            "type": "array",
            "minItems": 4,
            "maxItems": 6,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["title", "detail", "priority", "example_rewrite"],
                "properties": {
                    "title": {"type": "string"},
                    "detail": {"type": "string"},
                    "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                    "example_rewrite": {"type": "string"},
                },
            },
        },
        "next_prompt_recipe": {
            "type": "array",
            "minItems": 4,
            "maxItems": 7,
            "items": {"type": "string"},
        },
        "comparisons": {
            "type": "array",
            "minItems": 2,
            "maxItems": 4,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["label", "detail"],
                "properties": {
                    "label": {"type": "string"},
                    "detail": {"type": "string"},
                },
            },
        },
    },
}


def analyze_prompt_intelligence(
    payload: PromptIntelligenceAnalyzeRequest,
) -> PromptIntelligenceReportResponse:
    source_import = _resolve_source_import(payload)
    profile = get_prompt_profile()
    insights = get_profile_insights()
    messages = _flatten_messages(source_import)
    user_messages = [message for message in messages if message.role == "user"]
    if not user_messages:
        raise ValueError("Import did not include user prompts to analyze")

    report_payload, provider, model, status, metadata = _build_report_payload(
        source_import=source_import,
        user_messages=user_messages,
        profile_summary=profile.summary,
        insight_headline=insights.headline,
    )
    saved = _save_report(
        source_import=source_import,
        report_payload=report_payload,
        provider=provider,
        model=model,
        status=status,
        metadata=metadata,
    )
    store.record_audit_log(
        event_type="prompt_intelligence_analyzed",
        entity_type="prompt_intelligence_report",
        entity_id=saved.id,
        metadata={
            "import_id": source_import.id,
            "provider": provider,
            "model": model,
            "status": status,
        },
    )
    return _report_response(saved, source_import=source_import)


def list_prompt_intelligence_reports(limit: int = 12) -> list[PromptIntelligenceReportResponse]:
    with SessionLocal() as database:
        rows = list(
            database.scalars(
                select(PromptIntelligenceReport)
                .order_by(PromptIntelligenceReport.created_at.desc())
                .limit(limit)
            )
        )
    return [_report_response(row, include_source=False) for row in rows]


def get_prompt_intelligence_report(
    report_id: str,
) -> PromptIntelligenceReportResponse | None:
    with SessionLocal() as database:
        row = database.scalar(
            select(PromptIntelligenceReport).where(PromptIntelligenceReport.id == report_id)
        )
    return _report_response(row, include_source=True) if row else None


def get_latest_prompt_intelligence_report() -> PromptIntelligenceReportResponse | None:
    with SessionLocal() as database:
        row = database.scalar(
            select(PromptIntelligenceReport)
            .order_by(PromptIntelligenceReport.created_at.desc())
            .limit(1)
        )
    return _report_response(row, include_source=True) if row else None


def _resolve_source_import(
    payload: PromptIntelligenceAnalyzeRequest,
) -> ConversationImportResponse:
    if payload.import_id:
        import_row = get_conversation_import(payload.import_id)
        if import_row is None:
            raise ValueError("Import not found")
        return import_row

    import_payload = ConversationImportRequest(
        platform=payload.platform,
        source_type=payload.source_type,
        title=payload.title,
        raw_text=payload.raw_text or "",
    )
    return create_conversation_import(import_payload)


def _build_report_payload(
    *,
    source_import: ConversationImportResponse,
    user_messages: list[ImportedMessageResponse],
    profile_summary: dict[str, Any],
    insight_headline: str,
) -> tuple[dict[str, Any], str, str, str, dict[str, Any]]:
    settings = get_settings()
    fallback_payload = _heuristic_report(
        source_import=source_import,
        user_messages=user_messages,
        profile_summary=profile_summary,
        insight_headline=insight_headline,
    )
    if settings.llm_provider != "openai" or not settings.openai_api_key:
        return (
            fallback_payload,
            "deterministic",
            LOCAL_MODEL,
            "ready",
            {
                "report_version": REPORT_VERSION,
                "analysis_mode": "deterministic_fallback",
                "fallback_reason": "OpenAI provider is not configured",
            },
        )

    try:
        model_payload = _openai_report(
            source_import=source_import,
            user_messages=user_messages,
            profile_summary=profile_summary,
            insight_headline=insight_headline,
        )
    except Exception as exc:  # pragma: no cover - network/provider fallback.
        metadata = {
            "report_version": REPORT_VERSION,
            "analysis_mode": "openai_fallback",
            "fallback_reason": str(exc),
        }
        return fallback_payload, "deterministic", LOCAL_MODEL, "openai_fallback", metadata

    merged = {
        **fallback_payload,
        **model_payload,
        "evidence": fallback_payload["evidence"],
    }
    metadata = {
        "report_version": REPORT_VERSION,
        "analysis_mode": "openai_responses",
        "input_message_count": len(user_messages),
    }
    return merged, "openai", settings.default_model, "ready", metadata


def _openai_report(
    *,
    source_import: ConversationImportResponse,
    user_messages: list[ImportedMessageResponse],
    profile_summary: dict[str, Any],
    insight_headline: str,
) -> dict[str, Any]:
    from openai import OpenAI

    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    transcript = _model_transcript(user_messages)
    instructions = (
        "You are PromptPilot's prompt intelligence analyst. Judge the user's prompting "
        "behavior from their imported prompts, not the assistant answers. Be direct, witty "
        "but useful, evidence-backed, and focused on how they can improve their prompting. "
        "Do not generate a finished prompt for them. Explain their style, habits, blind "
        "spots, and next upgrades."
    )
    response = client.responses.create(
        model=settings.default_model,
        instructions=instructions,
        input=[
            {
                "role": "user",
                "content": (
                    "Analyze this imported prompt session.\n\n"
                    f"Platform: {source_import.platform}\n"
                    f"Source type: {source_import.source_type}\n"
                    f"Profile summary: {json.dumps(profile_summary, default=str)}\n"
                    f"Existing insight headline: {insight_headline}\n\n"
                    "User prompts only:\n"
                    f"{transcript}"
                ),
            }
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "prompt_intelligence_report",
                "strict": True,
                "schema": OPENAI_REPORT_SCHEMA,
            }
        },
    )
    text = getattr(response, "output_text", "") or ""
    if not text.strip():
        raise ValueError("OpenAI returned an empty report")
    return _coerce_report_payload(json.loads(text))


def _heuristic_report(
    *,
    source_import: ConversationImportResponse,
    user_messages: list[ImportedMessageResponse],
    profile_summary: dict[str, Any],
    insight_headline: str,
) -> dict[str, Any]:
    texts = [message.text for message in user_messages if message.text.strip()]
    joined = "\n".join(texts).lower()
    word_counts = [_word_count(text) for text in texts]
    avg_words = mean(word_counts) if word_counts else 0
    evidence_strings = [_excerpt(text, 160) for text in texts[:4]]
    message_count = len(texts)
    technical_hits = _term_count(joined, TECHNICAL_TERMS)
    action_hits = _term_count(joined, ACTION_TERMS)
    constraint_hits = _term_count(joined, CONSTRAINT_TERMS)
    evidence_hits = _term_count(joined, EVIDENCE_TERMS)

    scores = [
        _score(
            "goal_clarity",
            "Goal clarity",
            _clamp_int((action_hits / max(message_count, 1)) * 82 + 18),
            "You usually point at an outcome, but the finish line can be sharper.",
            "Name the deliverable, success criteria, and what done looks like.",
            evidence_strings,
        ),
        _score(
            "context_depth",
            "Context depth",
            _clamp_int((avg_words / 85) * 100),
            "Your imports show how much story you give the model before asking.",
            "Add the current state, prior attempts, constraints, and audience when stakes rise.",
            evidence_strings,
        ),
        _score(
            "constraint_specificity",
            "Constraint specificity",
            _clamp_int((constraint_hits / max(message_count, 1)) * 34 + 22),
            "Constraints appear, but they are not always organized as operating rules.",
            "Put must-haves, non-goals, tools, and boundaries in separate lines.",
            evidence_strings,
        ),
        _score(
            "evidence_discipline",
            "Evidence discipline",
            _clamp_int((evidence_hits / max(message_count, 1)) * 45 + 15),
            "Source and verification expectations are visible only when explicitly requested.",
            "Ask for evidence standards, source type, and uncertainty handling up front.",
            evidence_strings,
        ),
        _score(
            "iteration_signal",
            "Iteration signal",
            _clamp_int(min(message_count, 10) * 9 + (12 if "fix" in joined else 0)),
            "The session shape shows whether you steer once or refine repeatedly.",
            "Use short follow-up corrections after the first answer instead of restarting from scratch.",
            evidence_strings,
        ),
        _score(
            "platform_specificity",
            "Platform specificity",
            _clamp_int((technical_hits / max(message_count, 1)) * 42 + 20),
            "You give stronger prompts when the target tool or stack is concrete.",
            "Name the platform, files, API surface, output form, and verification command.",
            evidence_strings,
        ),
    ]

    weakest = sorted(scores, key=lambda item: item["score"])[:2]
    strongest = sorted(scores, key=lambda item: item["score"], reverse=True)[:2]
    headline = _headline(strongest, weakest)
    summary = (
        f"Based on {message_count} user prompt{'s' if message_count != 1 else ''} from "
        f"{source_import.platform}, your prompting style looks like: "
        f"{strongest[0]['label'].lower()} is a current strength, while "
        f"{weakest[0]['label'].lower()} is the highest-leverage upgrade. "
        f"{insight_headline}"
    )

    return {
        "headline": headline,
        "summary": summary,
        "style_scores": scores,
        "behavior_patterns": [
            {
                "title": "You ask for motion quickly",
                "detail": (
                    "The prompts tend to move straight into execution. That is efficient, "
                    "but it can leave the model guessing at hidden standards."
                ),
                "confidence": 0.74,
                "evidence": evidence_strings[:2],
            },
            {
                "title": "The best prompts carry platform context",
                "detail": (
                    "When the prompt mentions tools, code, APIs, or target systems, the "
                    "assistant gets a much cleaner contract."
                ),
                "confidence": 0.68 if technical_hits else 0.42,
                "evidence": evidence_strings[:2],
            },
            {
                "title": "Judgment beats formatting",
                "detail": (
                    "The useful signal is not whether the prompt is pretty. It is whether "
                    "the model can infer the goal, boundaries, evidence standard, and next action."
                ),
                "confidence": 0.8,
                "evidence": evidence_strings[:2],
            },
        ],
        "recommendations": _recommendations(weakest),
        "next_prompt_recipe": [
            "Goal: the exact outcome I want",
            "Context: what is true right now",
            "Constraints: tools, limits, non-goals, and risk boundaries",
            "Evidence: what the answer should cite, verify, or admit it cannot know",
            "Output: the shape, depth, and decision I need next",
        ],
        "comparisons": [
            {
                "label": "Codex-style work",
                "detail": "Your coding prompts improve when they include repo state, files, allowed edits, and verification commands.",
            },
            {
                "label": "Claude or ChatGPT-style work",
                "detail": "Your analysis prompts improve when you state audience, depth, examples, and what tradeoffs matter.",
            },
            {
                "label": "Prompt intelligence lens",
                "detail": "The app now scores behavior patterns, not prompt prettiness or template compliance.",
            },
        ],
        "evidence": [
            {
                "type": "imported_message",
                "label": "Imported prompt",
                "excerpt": _excerpt(message.text, 220),
                "imported_message_id": message.id,
                "confidence": 0.72,
            }
            for message in user_messages[:5]
        ],
        "report_metadata": {
            "profile_headline": profile_summary.get("headline"),
            "message_count": message_count,
            "average_user_prompt_words": round(avg_words, 1),
            "normalizer_version": source_import.import_metadata.get("normalizer_version"),
        },
    }


def _save_report(
    *,
    source_import: ConversationImportResponse,
    report_payload: dict[str, Any],
    provider: str,
    model: str,
    status: str,
    metadata: dict[str, Any],
) -> PromptIntelligenceReport:
    with SessionLocal() as database:
        profile = ensure_local_profile(database)
        import_row = database.scalar(
            select(ConversationImport).where(ConversationImport.id == source_import.id)
        )
        if import_row is None:
            raise ValueError("Import not found")
        report = PromptIntelligenceReport(
            profile_id=profile.id,
            import_id=source_import.id,
            provider=provider,
            model=model,
            status=status,
            headline=str(report_payload["headline"]),
            summary=str(report_payload["summary"]),
            style_scores=report_payload["style_scores"],
            behavior_patterns=report_payload["behavior_patterns"],
            recommendations=report_payload["recommendations"],
            next_prompt_recipe=report_payload["next_prompt_recipe"],
            comparisons=report_payload["comparisons"],
            evidence=report_payload["evidence"],
            report_metadata={
                **report_payload.get("report_metadata", {}),
                **metadata,
            },
        )
        database.add(report)
        database.commit()
        database.refresh(report)
        return report


def _report_response(
    row: PromptIntelligenceReport,
    *,
    source_import: ConversationImportResponse | None = None,
    include_source: bool = True,
) -> PromptIntelligenceReportResponse:
    resolved_source = source_import
    if include_source and resolved_source is None and row.import_id:
        resolved_source = get_conversation_import(row.import_id)
    return PromptIntelligenceReportResponse(
        id=row.id,
        profile_id=row.profile_id,
        import_id=row.import_id,
        provider=row.provider,
        model=row.model,
        status=row.status,
        headline=row.headline,
        summary=row.summary,
        style_scores=[
            PromptIntelligenceScore.model_validate(item)
            for item in (row.style_scores or [])
        ],
        behavior_patterns=[
            PromptBehaviorPattern.model_validate(item)
            for item in (row.behavior_patterns or [])
        ],
        recommendations=[
            PromptIntelligenceRecommendation.model_validate(item)
            for item in (row.recommendations or [])
        ],
        next_prompt_recipe=list(row.next_prompt_recipe or []),
        comparisons=[
            PromptIntelligenceComparison.model_validate(item)
            for item in (row.comparisons or [])
        ],
        evidence=[
            ProfileEvidenceReference.model_validate(item)
            for item in (row.evidence or [])
        ],
        report_metadata=row.report_metadata or {},
        source_import=resolved_source,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _flatten_messages(
    source_import: ConversationImportResponse,
) -> list[ImportedMessageResponse]:
    return [
        message
        for conversation in source_import.conversations
        for message in conversation.messages
    ]


def _coerce_report_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "headline": str(payload.get("headline") or "Prompt behavior profile"),
        "summary": str(payload.get("summary") or "Prompt intelligence report is ready."),
        "style_scores": [
            PromptIntelligenceScore.model_validate(item).model_dump()
            for item in payload.get("style_scores", [])
        ],
        "behavior_patterns": [
            PromptBehaviorPattern.model_validate(item).model_dump()
            for item in payload.get("behavior_patterns", [])
        ],
        "recommendations": [
            PromptIntelligenceRecommendation.model_validate(item).model_dump()
            for item in payload.get("recommendations", [])
        ],
        "next_prompt_recipe": [
            str(item) for item in payload.get("next_prompt_recipe", [])
        ],
        "comparisons": [
            PromptIntelligenceComparison.model_validate(item).model_dump()
            for item in payload.get("comparisons", [])
        ],
    }


def _model_transcript(user_messages: list[ImportedMessageResponse]) -> str:
    lines: list[str] = []
    remaining = MAX_MODEL_TRANSCRIPT_CHARS
    for index, message in enumerate(user_messages, start=1):
        text = message.text.strip()
        if not text or remaining <= 0:
            continue
        chunk = f"\n[{index}] {text}\n"
        lines.append(chunk[:remaining])
        remaining -= len(chunk)
    return "\n".join(lines)


def _recommendations(weakest_scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    priorities = {item["key"] for item in weakest_scores}
    recommendations = [
        {
            "title": "Put the finish line first",
            "detail": "Open with the exact outcome, then add context. The model should know what it is optimizing for before reading the backstory.",
            "priority": "high" if "goal_clarity" in priorities else "medium",
            "example_rewrite": "Goal: produce a Phase 16 readiness checklist for this repo, with blockers and verification commands.",
        },
        {
            "title": "Separate constraints from context",
            "detail": "Constraints hidden in prose are easy for models to miss. Give them their own short block.",
            "priority": "high" if "constraint_specificity" in priorities else "medium",
            "example_rewrite": "Constraints: no generated prompt page, OpenAI only, evidence-backed scores, README updated.",
        },
        {
            "title": "Ask for evidence behavior",
            "detail": "When accuracy matters, tell the assistant what to verify, cite, compare, or mark uncertain.",
            "priority": "high" if "evidence_discipline" in priorities else "medium",
            "example_rewrite": "Evidence: cite local files or official docs; flag assumptions separately.",
        },
        {
            "title": "Name the platform contract",
            "detail": "Codex, Claude, ChatGPT, Cursor, and Gemini reward different context. Say which one the prompt is for.",
            "priority": "high" if "platform_specificity" in priorities else "low",
            "example_rewrite": "Platform: Codex. Expected behavior: inspect files, patch code, run tests, report exact changes.",
        },
    ]
    return recommendations


def _score(
    key: str,
    label: str,
    score: int,
    explanation: str,
    improvement: str,
    evidence: list[str],
) -> dict[str, Any]:
    if score >= 78:
        verdict = "strong"
    elif score >= 58:
        verdict = "emerging"
    elif score >= 38:
        verdict = "thin"
    else:
        verdict = "quiet"
    return {
        "key": key,
        "label": label,
        "score": score,
        "verdict": verdict,
        "explanation": explanation,
        "improvement": improvement,
        "evidence": evidence[:3],
    }


def _headline(strongest: list[dict[str, Any]], weakest: list[dict[str, Any]]) -> str:
    if not strongest or not weakest:
        return "Your prompt style is still coming into focus"
    return (
        f"{strongest[0]['label']} leads; "
        f"{weakest[0]['label'].lower()} is the next upgrade"
    )


def _word_count(text: str) -> int:
    return len([word for word in text.split() if word.strip()])


def _term_count(text: str, terms: set[str]) -> int:
    return sum(text.count(term) for term in terms)


def _clamp_int(value: float) -> int:
    return max(0, min(100, round(value)))


def _excerpt(text: str, limit: int) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 3]}..."
