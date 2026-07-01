from app.schemas import PromptSettings


CODE_LIKE_DOMAINS = {
    "software_engineering",
    "code",
    "coding",
    "engineering",
    "data",
    "devops",
}

EVIDENCE_HEAVY_DOMAINS = {
    "learning_research",
    "health_wellness",
    "legal_financial",
    "research",
    "medical",
    "legal",
    "finance",
    "financial",
    "news",
}

CODE_NATIVE_PLATFORMS = {"codex", "cursor"}

SOURCE_REQUEST_TERMS = {
    "cite",
    "citation",
    "evidence",
    "official",
    "reference",
    "research",
    "source",
    "sources",
}

CODE_PLATFORM_BEHAVIOR = {
    "codex": (
        "Optimize for Codex. Emphasize repository context, relevant files, constraints, "
        "implementation steps, verification commands, and expected code-change behavior."
    ),
    "cursor": (
        "Optimize for Cursor. Emphasize files, editor context, incremental code edits, tests, "
        "and concise implementation notes."
    ),
}

GENERIC_PLATFORM_BEHAVIOR = {
    "codex": (
        "Optimize for Codex. Use crisp structure, explicit assumptions, numbered steps, and "
        "concise handoff wording suited to a paste-ready assistant prompt."
    ),
    "cursor": (
        "Optimize for Cursor as a structured assistant. Use concise context, clear steps, and "
        "practical next actions without assuming a software workspace."
    ),
}

PLATFORM_BEHAVIOR_SUMMARIES = {
    "codex": {
        "code": "repo context, file constraints, implementation steps, and verification",
        "generic": "structured steps, explicit assumptions, and concise handoff wording",
    },
    "cursor": {
        "code": "editor context, incremental edits, and test feedback",
        "generic": "concise context, clear steps, and practical next actions",
    },
    "claude": {
        "generic": "long-context structure, nuance, and labeled assumptions",
    },
    "chatgpt": {
        "generic": "portable, explicit, reusable instructions",
    },
    "gemini": {
        "generic": "broad context, source comparison when useful, and multimodal readiness",
    },
    "grok": {
        "generic": "direct framing, contrast, and concise iteration",
    },
    "perplexity": {
        "generic": "source-forward research, citations, and evidence boundaries",
    },
    "copilot": {
        "generic": "productivity workflow, document context, and concise execution",
    },
    "generic": {
        "generic": "provider-neutral instructions without platform assumptions",
    },
    "other": {
        "generic": "provider-neutral instructions without platform assumptions",
    },
}

PLATFORM_TERMS = {
    "codex": {
        "code": {"codex", "repository", "repo", "files", "verification", "code-change"},
        "generic": {"codex", "structured", "assumptions", "steps", "handoff"},
    },
    "cursor": {
        "code": {"cursor", "editor", "files", "incremental", "tests"},
        "generic": {"cursor", "structured", "context", "steps", "actions"},
    },
    "claude": {"generic": {"claude", "long-context", "nuanced", "tradeoffs", "assumptions"}},
    "chatgpt": {"generic": {"chatgpt", "portable", "general-purpose", "reuse"}},
    "gemini": {"generic": {"gemini", "multimodal", "research", "sources"}},
    "grok": {"generic": {"grok", "direct", "current", "concise", "contrast"}},
    "perplexity": {"generic": {"perplexity", "sources", "research", "citations", "evidence"}},
    "copilot": {"generic": {"copilot", "microsoft", "document", "workflow", "productivity"}},
    "generic": {"generic": {"generic", "provider-specific", "assumptions"}},
    "other": {"generic": {"generic", "provider-specific", "assumptions"}},
}


def is_code_like_domain(domain: str | None) -> bool:
    return _normalize_domain(domain) in CODE_LIKE_DOMAINS


def is_evidence_heavy_domain(domain: str | None) -> bool:
    return _normalize_domain(domain) in EVIDENCE_HEAVY_DOMAINS


def has_executable_environment(domain: str | None) -> bool:
    return is_code_like_domain(domain)


def uses_code_platform_scaffolding(platform: str, domain: str | None) -> bool:
    return platform in CODE_NATIVE_PLATFORMS and is_code_like_domain(domain)


def effective_source_strictness(
    settings: PromptSettings,
    domain: str | None,
    raw_input: str = "",
    intent: str | None = None,
) -> str:
    if settings.source_strictness != "evidence_first":
        return settings.source_strictness
    if is_evidence_heavy_domain(domain) or _asks_for_sources(raw_input) or intent == "research":
        return settings.source_strictness
    if settings.sources in {"web", "official_docs"}:
        return "cite_when_needed"
    return "none"


def effective_interaction_mode(settings: PromptSettings, domain: str | None) -> str:
    if settings.interaction_mode == "agentic" and not has_executable_environment(domain):
        return "guide"
    return settings.interaction_mode


def platform_behavior(platform: str, domain: str | None) -> str:
    if uses_code_platform_scaffolding(platform, domain):
        return CODE_PLATFORM_BEHAVIOR[platform]
    if platform in GENERIC_PLATFORM_BEHAVIOR:
        return GENERIC_PLATFORM_BEHAVIOR[platform]
    return {
        "claude": (
            "Optimize for Claude. Support long-context analysis, careful structure, nuanced "
            "tradeoffs, and a deliberate answer with clearly labeled assumptions."
        ),
        "chatgpt": (
            "Optimize for ChatGPT. Keep the prompt portable, explicit, general-purpose, and easy to reuse."
        ),
        "gemini": (
            "Optimize for Gemini. Mention multimodal inputs, broad research context, and source comparison when relevant."
        ),
        "grok": (
            "Optimize for Grok. Keep the prompt direct, contrastive, current-context aware, and easy to iterate."
        ),
        "perplexity": (
            "Optimize for Perplexity. Emphasize source-backed research, citations, evidence boundaries, and comparison of claims."
        ),
        "copilot": (
            "Optimize for Copilot. Emphasize concise workflow context, document context, and practical next actions."
        ),
        "generic": (
            "Optimize for a generic AI assistant. Avoid provider-specific features or assumptions."
        ),
        "other": (
            "Optimize for a generic AI assistant. Avoid provider-specific features or assumptions."
        ),
    }.get(
        platform,
        "Optimize for a generic AI assistant. Avoid provider-specific features or assumptions.",
    )


def platform_behavior_summary(platform: str, domain: str | None) -> str:
    summary = PLATFORM_BEHAVIOR_SUMMARIES.get(platform, PLATFORM_BEHAVIOR_SUMMARIES["generic"])
    if uses_code_platform_scaffolding(platform, domain):
        return summary.get("code", summary["generic"])
    return summary["generic"]


def platform_fit_terms(platform: str, domain: str | None) -> set[str]:
    terms = PLATFORM_TERMS.get(platform, PLATFORM_TERMS["generic"])
    if uses_code_platform_scaffolding(platform, domain):
        return terms.get("code", terms["generic"])
    return terms["generic"]


def _asks_for_sources(raw_input: str) -> bool:
    lowered = raw_input.lower()
    return any(term in lowered for term in SOURCE_REQUEST_TERMS)


def _normalize_domain(domain: str | None) -> str:
    return str(domain or "").strip().lower()
