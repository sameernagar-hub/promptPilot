from app.models import PromptVariant
from app.schemas import PromptSettings


SCORING_KEYS = [
    "clarity",
    "specificity",
    "safety",
    "actionability",
    "domain_fit",
    "beginner_friendliness",
    "expected_answer_quality",
]

STRATEGY_PRIORITY = {
    "safety_first": 0,
    "diagnostic": 1,
    "questions_first": 2,
    "beginner_step_by_step": 3,
    "expert_consultant": 4,
    "comparison": 5,
}


def _score_prompt(
    problem: str,
    prompt: PromptVariant,
    settings: PromptSettings,
    risk_level: str | None = None,
    needs_clarification: bool = False,
) -> dict[str, float]:
    text = prompt.prompt_text.lower()
    problem_terms = {term.strip(".,:;!?()[]") for term in problem.lower().split()}
    matched_terms = [term for term in problem_terms if len(term) > 3 and term in text]
    is_safety_first = prompt.strategy == "safety_first"
    is_questions_first = prompt.strategy == "questions_first"
    is_beginner = prompt.strategy == "beginner_step_by_step"
    is_expert = prompt.strategy == "expert_consultant"
    is_comparison = prompt.strategy == "comparison"
    risk_bonus = risk_level in {"medium", "high"} or settings.risk == "safe_only"

    scores = {
        "clarity": 0.86 if is_questions_first else 0.82,
        "specificity": min(0.95, 0.58 + (0.04 * len(matched_terms))),
        "safety": 0.96 if is_safety_first else (0.9 if "risk" in text or "safest" in text else 0.74),
        "actionability": 0.9 if "next" in text or "plan" in text else 0.72,
        "domain_fit": min(0.94, 0.64 + (0.03 * len(matched_terms))),
        "beginner_friendliness": 0.94 if settings.skill_level == "beginner" or is_beginner else 0.78,
        "expected_answer_quality": 0.88 if is_expert or is_comparison else 0.84,
    }
    if risk_bonus and is_safety_first:
        scores["safety"] = 0.99
        scores["expected_answer_quality"] = max(scores["expected_answer_quality"], 0.88)
    if needs_clarification and is_questions_first:
        scores["clarity"] = 0.94
        scores["specificity"] = max(scores["specificity"], 0.86)
    if settings.format == "table" and is_comparison:
        scores["clarity"] = max(scores["clarity"], 0.9)
    return {key: round(scores[key], 2) for key in SCORING_KEYS}


def score_prompt_variants(
    problem: str,
    prompts: list[PromptVariant],
    settings: PromptSettings,
    risk_level: str | None = None,
    needs_clarification: bool = False,
) -> list[PromptVariant]:
    scored: list[PromptVariant] = []
    for prompt in prompts:
        prompt.score_breakdown = _score_prompt(
            problem,
            prompt,
            settings,
            risk_level=risk_level,
            needs_clarification=needs_clarification,
        )
        prompt.score_total = round(
            sum(prompt.score_breakdown.values()) / len(prompt.score_breakdown),
            2,
        )
        prompt.explanation = (
            f"Scores emphasize {prompt.strategy.replace('_', ' ')} using deterministic "
            "Phase 5 rules across clarity, specificity, safety, actionability, domain fit, "
            "beginner friendliness, and expected answer quality."
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
