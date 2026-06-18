from app.models import PromptVariant
from app.schemas import PromptSettings


SCORING_KEYS = [
    "clarity",
    "specificity",
    "safety",
    "actionability",
    "domain_fit",
    "platform_fit",
    "beginner_friendliness",
    "expected_answer_quality",
]

STRATEGY_PRIORITY = {
    "recommended_prompt": 0,
    "safety_first": 1,
    "diagnostic": 2,
    "questions_first": 3,
    "beginner_step_by_step": 4,
    "expert_consultant": 5,
    "comparison": 6,
}


PLATFORM_TERMS = {
    "codex": {"codex", "repository", "repo", "files", "verification", "code-change"},
    "claude": {"claude", "long-context", "nuanced", "tradeoffs", "assumptions"},
    "chatgpt": {"chatgpt", "portable", "general-purpose", "reuse"},
    "gemini": {"gemini", "multimodal", "research", "sources"},
    "cursor": {"cursor", "editor", "files", "incremental", "tests"},
    "generic": {"generic", "provider-specific", "assumptions"},
}


def _score_prompt(
    problem: str,
    prompt: PromptVariant,
    settings: PromptSettings,
    risk_level: str | None = None,
    needs_clarification: bool = False,
    missing_context_count: int = 0,
) -> dict[str, float]:
    text = prompt.prompt_text.lower()
    problem_terms = {term.strip(".,:;!?()[]") for term in problem.lower().split()}
    matched_terms = [term for term in problem_terms if len(term) > 3 and term in text]
    is_safety_first = prompt.strategy == "safety_first"
    is_recommended = prompt.strategy == "recommended_prompt"
    is_questions_first = prompt.strategy == "questions_first"
    is_beginner = prompt.strategy == "beginner_step_by_step"
    is_expert = prompt.strategy == "expert_consultant"
    is_comparison = prompt.strategy == "comparison"
    risk_bonus = risk_level in {"medium", "high"} or settings.risk == "safe_only"

    scores = {
        "clarity": 0.9 if is_recommended else (0.86 if is_questions_first else 0.82),
        "specificity": min(0.95, 0.58 + (0.04 * len(matched_terms))),
        "safety": 0.96 if is_safety_first else (0.9 if "risk" in text or "safest" in text else 0.74),
        "actionability": 0.94 if is_recommended else (0.9 if "next" in text or "plan" in text else 0.72),
        "domain_fit": min(0.94, 0.64 + (0.03 * len(matched_terms))),
        "platform_fit": _platform_fit_score(text, settings),
        "beginner_friendliness": 0.94 if settings.skill_level == "beginner" or is_beginner else 0.78,
        "expected_answer_quality": 0.9 if is_recommended or is_expert or is_comparison else 0.84,
    }
    if risk_bonus and is_safety_first:
        scores["safety"] = 0.99
        scores["expected_answer_quality"] = max(scores["expected_answer_quality"], 0.88)
    if is_recommended:
        scores["specificity"] = max(scores["specificity"], 0.9)
        scores["safety"] = max(scores["safety"], 0.88)
        scores["domain_fit"] = max(scores["domain_fit"], 0.9)
        scores["platform_fit"] = max(scores["platform_fit"], 0.9)
        scores["beginner_friendliness"] = max(scores["beginner_friendliness"], 0.84)
    if needs_clarification and is_questions_first:
        scores["clarity"] = 0.94
        scores["specificity"] = max(scores["specificity"], 0.86)
    if missing_context_count:
        penalty = min(0.12, missing_context_count * 0.03)
        scores["specificity"] = max(0.58, scores["specificity"] - penalty)
        scores["expected_answer_quality"] = max(0.62, scores["expected_answer_quality"] - (penalty / 2))
    if settings.format == "table" and is_comparison:
        scores["clarity"] = max(scores["clarity"], 0.9)
    return {key: round(scores[key], 2) for key in SCORING_KEYS}


def _platform_fit_score(text: str, settings: PromptSettings) -> float:
    target_terms = PLATFORM_TERMS.get(settings.target_platform, PLATFORM_TERMS["generic"])
    matched = sum(1 for term in target_terms if term in text)
    base = 0.62 + (matched * 0.07)
    if f"target platform: {settings.target_platform}" in text:
        base += 0.1
    if settings.target_platform == "generic" and "provider-specific" in text:
        base += 0.08
    return round(min(0.96, base), 2)


def score_prompt_variants(
    problem: str,
    prompts: list[PromptVariant],
    settings: PromptSettings,
    risk_level: str | None = None,
    needs_clarification: bool = False,
    missing_context_count: int = 0,
    recommendation_notes: list[str] | None = None,
) -> list[PromptVariant]:
    scored: list[PromptVariant] = []
    for prompt in prompts:
        prompt.score_breakdown = _score_prompt(
            problem,
            prompt,
            settings,
            risk_level=risk_level,
            needs_clarification=needs_clarification,
            missing_context_count=missing_context_count,
        )
        prompt.score_total = round(
            sum(prompt.score_breakdown.values()) / len(prompt.score_breakdown),
            2,
        )
        prompt.explanation = _explanation_for_prompt(
            prompt,
            settings,
            missing_context_count=missing_context_count,
            recommendation_notes=recommendation_notes or [],
        )
        scored.append(prompt)

    scored.sort(
        key=lambda item: (
            -(item.score_total or 0),
            STRATEGY_PRIORITY.get(item.strategy, 99),
            item.title,
        )
    )
    for index, prompt in enumerate(scored):
        prompt.recommendation_label = "recommended" if index == 0 else "candidate"
    return scored


def _explanation_for_prompt(
    prompt: PromptVariant,
    settings: PromptSettings,
    missing_context_count: int,
    recommendation_notes: list[str],
) -> str:
    notes = [
        f"{settings.target_platform} platform",
        f"{settings.format} format",
        f"{settings.tone} tone",
        f"{settings.detail_level} detail",
    ]
    notes.extend(recommendation_notes[:4])
    if missing_context_count:
        notes.append(f"{missing_context_count} skipped or missing context assumptions")
    note_text = "; ".join(notes)
    return (
        f"This {prompt.strategy.replace('_', ' ')} draft was shaped by {note_text}. "
        "Scores still use deterministic rules for clarity, specificity, safety, actionability, "
        "domain fit, platform fit, beginner friendliness, and expected answer quality."
    )
