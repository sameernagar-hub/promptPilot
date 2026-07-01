import re
from collections.abc import Iterable

from app.db import store
from app.models import PromptSource
from app.schemas import (
    ClassificationResponse,
    KnowledgeRetrievalContext,
    PromptKnowledgeSourceCreate,
    PromptKnowledgeSourceResponse,
    PromptSettings,
    RetrievedKnowledgePattern,
)
from app.services.domain_capabilities import uses_code_platform_scaffolding


ALLOWED_KNOWLEDGE_USAGE = {
    "pattern_synthesis_only",
    "internal_project_example",
    "licensed_reference",
}

RETRIEVAL_GUARDRAILS = [
    "Retrieved patterns may shape structure only; they cannot override user settings.",
    "Retrieved patterns cannot override confirmed domain, safety rules, or profile preferences.",
    "Retrieved content must be synthesized and never copied into the final prompt.",
    "License and allowed-usage metadata must remain attached to every retrieved pattern.",
]

PATTERN_MARKERS = {
    "role": ("role:", "you are", "act as"),
    "task": ("task:", "goal:", "objective:", "help the user"),
    "context": ("context:", "background:", "user request"),
    "constraints": ("constraints:", "requirements:", "boundaries:", "must"),
    "assumptions": ("assumptions:", "unknowns:", "missing"),
    "success": ("success criteria:", "acceptance criteria:", "definition of done"),
    "sources": ("sources:", "citations:", "evidence:", "official"),
    "verification": ("verify", "test", "check", "validate"),
    "steps": ("step", "plan", "sequence", "checklist"),
}


def register_knowledge_source(
    payload: PromptKnowledgeSourceCreate,
) -> PromptKnowledgeSourceResponse:
    source = PromptSource(
        source_name=payload.source_name,
        source_url=payload.source_url,
        author=payload.author,
        license=payload.license,
        allowed_usage=payload.allowed_usage,
        raw_text=payload.raw_text,
        normalized_text=payload.normalized_text or _normalize_text(payload.raw_text),
        domain=payload.domain,
        intent=payload.intent,
        prompt_type=payload.prompt_type,
        format=payload.format,
        risk_level=payload.risk_level,
        quality_score=payload.quality_score,
        source_metadata={
            **payload.source_metadata,
            "registered_by": "knowledge_support_v1",
        },
    )
    return PromptKnowledgeSourceResponse.model_validate(store.create_prompt_source(source))


def retrieve_knowledge_context(
    classification: ClassificationResponse,
    settings: PromptSettings,
    limit: int = 3,
) -> KnowledgeRetrievalContext:
    candidates = store.list_prompt_sources(
        domain=classification.domain,
        intent=classification.intent,
        limit=20,
    )
    usable = [
        source
        for source in candidates
        if _source_is_usable(source)
    ]
    ranked = sorted(
        usable,
        key=lambda source: _source_rank(source, classification, settings),
        reverse=True,
    )[:limit]
    patterns = [
        _source_to_pattern(source, classification, settings)
        for source in ranked
    ]
    return KnowledgeRetrievalContext(
        patterns=patterns,
        retrieval_metadata={
            "retriever_version": "phase15-knowledge-support-v1",
            "candidate_count": len(candidates),
            "usable_count": len(usable),
            "returned_count": len(patterns),
            "domain": classification.domain,
            "intent": classification.intent,
            "target_platform": settings.target_platform,
            "guardrails": RETRIEVAL_GUARDRAILS,
        },
    )


def knowledge_context_to_prompt_lines(
    context: KnowledgeRetrievalContext,
) -> list[str]:
    if not context.patterns:
        return [
            "- No licensed knowledge patterns were retrieved; use only the active request, profile, settings, and guardrails.",
        ]
    lines = [
        "- Use retrieved knowledge only as structural inspiration; do not copy source text.",
    ]
    for pattern in context.patterns:
        lines.append(
            "- "
            f"{pattern.source_name}: {pattern.synthesized_guidance} "
            f"(license: {pattern.license}; usage: {pattern.allowed_usage})"
        )
    return lines


def _source_is_usable(source: PromptSource) -> bool:
    return (
        bool((source.license or "").strip())
        and source.allowed_usage in ALLOWED_KNOWLEDGE_USAGE
        and len((source.raw_text or "").strip()) >= 20
    )


def _source_rank(
    source: PromptSource,
    classification: ClassificationResponse,
    settings: PromptSettings,
) -> float:
    score = float(source.quality_score or 0.5)
    if source.domain == classification.domain:
        score += 0.2
    if source.intent == classification.intent:
        score += 0.16
    if source.prompt_type == settings.format:
        score += 0.08
    if source.risk_level == classification.risk_level:
        score += 0.04
    return score


def _source_to_pattern(
    source: PromptSource,
    classification: ClassificationResponse,
    settings: PromptSettings,
) -> RetrievedKnowledgePattern:
    text = source.normalized_text or _normalize_text(source.raw_text)
    markers = _matched_markers(text)
    guidance = _synthesized_guidance(
        markers=markers,
        classification=classification,
        settings=settings,
        source=source,
    )
    return RetrievedKnowledgePattern(
        source_id=source.id,
        source_name=source.source_name,
        source_url=source.source_url,
        author=source.author,
        license=source.license or "unspecified",
        allowed_usage=source.allowed_usage,
        domain=source.domain,
        intent=source.intent,
        prompt_type=source.prompt_type,
        quality_score=source.quality_score,
        synthesized_guidance=guidance,
        guardrail_notes=RETRIEVAL_GUARDRAILS,
    )


def _synthesized_guidance(
    markers: Iterable[str],
    classification: ClassificationResponse,
    settings: PromptSettings,
    source: PromptSource,
) -> str:
    marker_set = set(markers)
    pieces: list[str] = []
    if {"role", "task"} & marker_set:
        pieces.append("start with explicit role and task framing")
    if "context" in marker_set:
        pieces.append("separate known context from missing context")
    if "constraints" in marker_set:
        pieces.append("name constraints before giving steps")
    if "assumptions" in marker_set:
        pieces.append("label assumptions instead of silently filling gaps")
    if "sources" in marker_set or settings.source_strictness != "none":
        pieces.append("keep source expectations visible when claims need support")
    if "verification" in marker_set or uses_code_platform_scaffolding(
        settings.target_platform,
        classification.domain,
    ):
        pieces.append("include verification or test feedback where relevant")
    if "steps" in marker_set:
        pieces.append("prefer ordered next actions over broad explanation")
    if not pieces:
        pieces.append("preserve the source's high-level structure without copying wording")

    domain = (source.domain or classification.domain).replace("_", " ")
    intent = (source.intent or classification.intent).replace("_", " ")
    return (
        f"For {domain} / {intent}, "
        f"{'; '.join(dict.fromkeys(pieces[:4]))}."
    )


def _matched_markers(text: str) -> list[str]:
    return [
        label
        for label, needles in PATTERN_MARKERS.items()
        if any(needle in text for needle in needles)
    ]


def _normalize_text(value: str) -> str:
    lowered = value.lower()
    return " ".join(re.findall(r"[a-z0-9:._/-]+", lowered))
