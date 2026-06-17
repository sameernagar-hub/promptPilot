from dataclasses import dataclass
from typing import Any

from app.schemas import ClassificationResponse


@dataclass(frozen=True)
class DomainDefinition:
    key: str
    label: str
    subdomain: str
    keywords: set[str]


DOMAIN_DEFINITIONS = [
    DomainDefinition(
        key="bicycle_repair",
        label="Bicycle repair",
        subdomain="mechanical troubleshooting",
        keywords={
            "bike",
            "bicycle",
            "chain",
            "derailleur",
            "gear",
            "pedal",
            "tire",
            "tube",
            "brake",
            "spoke",
            "wheel",
        },
    ),
    DomainDefinition(
        key="automotive_repair",
        label="Automotive repair",
        subdomain="vehicle troubleshooting",
        keywords={
            "car",
            "truck",
            "engine",
            "battery",
            "alternator",
            "radiator",
            "oil",
            "transmission",
            "starter",
            "garage",
        },
    ),
    DomainDefinition(
        key="home_repair",
        label="Home repair",
        subdomain="household troubleshooting",
        keywords={
            "sink",
            "leak",
            "pipe",
            "furnace",
            "breaker",
            "outlet",
            "appliance",
            "dishwasher",
            "washer",
            "plumbing",
        },
    ),
    DomainDefinition(
        key="software_engineering",
        label="Software engineering",
        subdomain="code and product building",
        keywords={
            "api",
            "app",
            "bug",
            "code",
            "database",
            "deploy",
            "fastapi",
            "next.js",
            "python",
            "react",
            "repo",
            "typescript",
            "docker",
        },
    ),
    DomainDefinition(
        key="writing_communication",
        label="Writing and communication",
        subdomain="message drafting",
        keywords={
            "email",
            "memo",
            "proposal",
            "manager",
            "client",
            "resume",
            "cover letter",
            "presentation",
            "message",
            "copy",
        },
    ),
    DomainDefinition(
        key="learning_research",
        label="Learning and research",
        subdomain="explanation and study",
        keywords={
            "explain",
            "learn",
            "research",
            "study",
            "summarize",
            "compare",
            "teach",
            "understand",
            "topic",
            "sources",
        },
    ),
    DomainDefinition(
        key="business_strategy",
        label="Business strategy",
        subdomain="planning and decisions",
        keywords={
            "business",
            "startup",
            "market",
            "pricing",
            "customers",
            "strategy",
            "sales",
            "growth",
            "roadmap",
        },
    ),
    DomainDefinition(
        key="health_wellness",
        label="Health and wellness",
        subdomain="health information",
        keywords={
            "doctor",
            "medical",
            "symptom",
            "medicine",
            "pain",
            "diet",
            "workout",
            "fitness",
            "sleep",
            "therapy",
        },
    ),
    DomainDefinition(
        key="legal_financial",
        label="Legal or financial",
        subdomain="high-stakes decision support",
        keywords={
            "legal",
            "contract",
            "lawyer",
            "financial",
            "tax",
            "investment",
            "insurance",
            "loan",
            "debt",
            "compliance",
        },
    ),
    DomainDefinition(
        key="creative_media",
        label="Creative media",
        subdomain="creative production",
        keywords={
            "video",
            "story",
            "script",
            "brand",
            "design",
            "image",
            "music",
            "campaign",
            "portfolio",
        },
    ),
]

INTENT_KEYWORDS = {
    "troubleshoot": {
        "bug",
        "broken",
        "clicks",
        "error",
        "fails",
        "fix",
        "issue",
        "leak",
        "not working",
        "problem",
        "repair",
        "stale",
        "won't",
    },
    "build": {"build", "create", "make", "implement", "scaffold", "develop", "start"},
    "write": {"write", "draft", "rewrite", "email", "letter", "message", "proposal"},
    "learn": {"learn", "explain", "teach", "understand", "study"},
    "compare": {"compare", "choose", "versus", "vs", "tradeoff", "options"},
    "research": {"research", "sources", "evidence", "summarize", "investigate"},
    "plan": {"plan", "roadmap", "phases", "workflow", "strategy"},
}

RISK_KEYWORDS = {
    "high": {
        "brake",
        "gas",
        "electrical panel",
        "medical",
        "legal",
        "financial",
        "injury",
        "fire",
        "smoke",
        "carbon monoxide",
        "tax",
        "contract",
    },
    "medium": {
        "electrical",
        "plumbing",
        "insurance",
        "security",
        "production",
        "deployment",
        "health",
        "repair",
    },
}

AMBIGUOUS_TERMS = {"bike", "repair", "fix", "problem", "help", "thing", "stuff"}


def classify_problem(problem: str) -> ClassificationResponse:
    domain_rankings = _rank_domains(problem)
    top_domain, top_signals = domain_rankings[0]
    if not top_signals:
        top_domain = _generic_domain()

    intent, intent_signals = _detect_intent(problem)
    risk_level, risk_signals = _detect_risk(problem)
    evidence = _evidence(top_domain, top_signals, intent, intent_signals, risk_signals)
    alternatives = [
        definition.key
        for definition, signals in domain_rankings[1:4]
        if signals
    ]
    all_signals = sorted(set(top_signals + intent_signals + risk_signals))
    confidence = _confidence(top_signals, intent_signals, risk_signals, alternatives)
    needs_confirmation = _needs_confirmation(problem, confidence, top_signals, alternatives)

    return ClassificationResponse(
        domain=top_domain.key,
        primary_domain=top_domain.key,
        subdomain=top_domain.subdomain,
        intent=intent,
        risk_level=risk_level,
        confidence=confidence,
        signals=all_signals,
        evidence=evidence,
        alternative_domains=alternatives,
        needs_domain_confirmation=needs_confirmation,
        confirmed_domain=None,
        domain_source="detected",
    )


def apply_domain_confirmation(
    classification: ClassificationResponse,
    confirmed_domain: str,
    accepted: bool,
) -> ClassificationResponse:
    normalized = _normalize_domain_key(confirmed_domain)
    source = "user_confirmed" if accepted and normalized == classification.primary_domain else "user_corrected"
    definition = _definition_for_key(normalized)
    return classification.model_copy(
        update={
            "domain": normalized,
            "primary_domain": normalized,
            "subdomain": definition.subdomain if definition else classification.subdomain,
            "confirmed_domain": normalized,
            "domain_source": source,
            "needs_domain_confirmation": False,
        }
    )


def _rank_domains(problem: str) -> list[tuple[DomainDefinition, list[str]]]:
    rankings = [
        (definition, _matches(problem, definition.keywords))
        for definition in DOMAIN_DEFINITIONS
    ]
    return sorted(
        rankings,
        key=lambda item: (len(item[1]), _specificity_score(item[1]), item[0].key),
        reverse=True,
    )


def _detect_intent(problem: str) -> tuple[str, list[str]]:
    intent_scores = {
        intent: _matches(problem, keywords)
        for intent, keywords in INTENT_KEYWORDS.items()
    }
    intent, intent_signals = max(
        intent_scores.items(),
        key=lambda item: (len(item[1]), item[0]),
    )
    if not intent_signals:
        return "clarify_and_plan", []
    return intent, intent_signals


def _detect_risk(problem: str) -> tuple[str, list[str]]:
    high_risk_signals = _matches(problem, RISK_KEYWORDS["high"])
    medium_risk_signals = _matches(problem, RISK_KEYWORDS["medium"])
    if high_risk_signals:
        return "high", high_risk_signals
    if medium_risk_signals:
        return "medium", medium_risk_signals
    return "low", []


def _matches(problem: str, keywords: set[str]) -> list[str]:
    lowered = problem.lower()
    return sorted(keyword for keyword in keywords if keyword in lowered)


def _confidence(
    domain_signals: list[str],
    intent_signals: list[str],
    risk_signals: list[str],
    alternatives: list[str],
) -> float:
    signal_count = len(set(domain_signals + intent_signals + risk_signals))
    confidence = 0.32 + (0.12 * len(set(domain_signals))) + (0.05 * signal_count)
    if alternatives:
        confidence -= min(0.16, 0.05 * len(alternatives))
    return round(max(0.25, min(0.95, confidence)), 2)


def _needs_confirmation(
    problem: str,
    confidence: float,
    domain_signals: list[str],
    alternatives: list[str],
) -> bool:
    lowered = problem.lower()
    ambiguous_signal = any(term in lowered for term in AMBIGUOUS_TERMS)
    return confidence < 0.72 or ambiguous_signal or bool(alternatives)


def _evidence(
    domain: DomainDefinition,
    domain_signals: list[str],
    intent: str,
    intent_signals: list[str],
    risk_signals: list[str],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if domain_signals:
        items.append(
            {
                "type": "domain_keyword",
                "label": domain.label,
                "signals": domain_signals,
            }
        )
    if intent_signals:
        items.append(
            {
                "type": "intent_keyword",
                "label": intent,
                "signals": intent_signals,
            }
        )
    if risk_signals:
        items.append(
            {
                "type": "risk_keyword",
                "label": "risk",
                "signals": risk_signals,
            }
        )
    return items


def _specificity_score(signals: list[str]) -> int:
    return sum(len(signal) for signal in signals)


def _normalize_domain_key(value: str) -> str:
    cleaned = value.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "bike": "bicycle_repair",
        "bicycle": "bicycle_repair",
        "bicycle_repair": "bicycle_repair",
        "bike_repair": "bicycle_repair",
        "car": "automotive_repair",
        "car_repair": "automotive_repair",
        "software": "software_engineering",
        "coding": "software_engineering",
        "home": "home_repair",
        "writing": "writing_communication",
        "research": "learning_research",
    }
    return aliases.get(cleaned, cleaned)


def _definition_for_key(key: str) -> DomainDefinition | None:
    return next((definition for definition in DOMAIN_DEFINITIONS if definition.key == key), None)


def _generic_domain() -> DomainDefinition:
    return DomainDefinition(
        key="general_problem_solving",
        label="General problem solving",
        subdomain="open-ended request",
        keywords=set(),
    )
