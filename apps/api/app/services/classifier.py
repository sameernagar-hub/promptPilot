from app.schemas import ClassificationResponse


DOMAIN_KEYWORDS = {
    "car_home_troubleshooting": {
        "car",
        "truck",
        "engine",
        "battery",
        "sink",
        "leak",
        "pipe",
        "furnace",
        "breaker",
        "outlet",
        "garage",
        "appliance",
        "dishwasher",
        "washer",
    },
    "software_project_building": {
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
        "state",
        "typescript",
    },
    "writing_business_communication": {
        "email",
        "memo",
        "proposal",
        "manager",
        "client",
        "resume",
        "cover letter",
        "presentation",
        "message",
    },
    "learning_research": {
        "explain",
        "learn",
        "research",
        "study",
        "summarize",
        "compare",
        "teach",
        "understand",
        "topic",
    },
}

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
        "stale",
        "won't",
    },
    "build": {"build", "create", "make", "implement", "scaffold", "develop", "start"},
    "write": {"write", "draft", "rewrite", "email", "letter", "message", "proposal"},
    "learn": {"learn", "explain", "teach", "understand", "study"},
    "compare": {"compare", "choose", "versus", "vs", "tradeoff", "options"},
    "research": {"research", "sources", "evidence", "summarize", "investigate"},
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
    },
    "medium": {
        "electrical",
        "plumbing",
        "insurance",
        "tax",
        "contract",
        "security",
        "production",
        "deployment",
    },
}


def _matches(problem: str, keywords: set[str]) -> list[str]:
    lowered = problem.lower()
    return sorted(keyword for keyword in keywords if keyword in lowered)


def classify_problem(problem: str) -> ClassificationResponse:
    domain_scores = {
        domain: _matches(problem, keywords)
        for domain, keywords in DOMAIN_KEYWORDS.items()
    }
    domain, signals = max(
        domain_scores.items(),
        key=lambda item: len(item[1]),
    )
    if not signals:
        domain = "general_problem_solving"

    intent_scores = {
        intent: _matches(problem, keywords)
        for intent, keywords in INTENT_KEYWORDS.items()
    }
    intent, intent_signals = max(
        intent_scores.items(),
        key=lambda item: len(item[1]),
    )
    if not intent_signals:
        intent = "clarify_and_plan"

    high_risk_signals = _matches(problem, RISK_KEYWORDS["high"])
    medium_risk_signals = _matches(problem, RISK_KEYWORDS["medium"])
    if high_risk_signals:
        risk_level = "high"
    elif medium_risk_signals:
        risk_level = "medium"
    else:
        risk_level = "low"

    all_signals = signals + intent_signals + high_risk_signals + medium_risk_signals
    confidence = min(0.95, 0.45 + (0.1 * len(set(all_signals))))

    return ClassificationResponse(
        domain=domain,
        intent=intent,
        risk_level=risk_level,
        confidence=round(confidence, 2),
        signals=sorted(set(all_signals)),
    )
