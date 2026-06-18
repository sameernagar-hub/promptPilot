from typing import Any

from app.schemas import ClarifyingQuestion, ClassificationResponse


DOMAIN_QUESTIONS = {
    "bicycle_repair": [
        (
            "symptoms",
            "What exactly is wrong with the bike?",
            "A repair prompt needs the observed symptom before suggesting diagnostics.",
        ),
        (
            "bike_context",
            "What kind of bike is it, and what changed recently?",
            "Bike type and recent changes narrow the likely mechanical causes.",
        ),
    ],
    "automotive_repair": [
        (
            "symptoms",
            "What exact symptoms do you see, hear, smell, or notice?",
            "The prompt needs observable details before suggesting diagnostics.",
        ),
        (
            "recent_changes",
            "What changed recently, and what have you already tried?",
            "Recent changes and attempted fixes narrow the likely causes.",
        ),
    ],
    "home_repair": [
        (
            "symptoms",
            "What exact symptoms do you see, hear, smell, or notice?",
            "The prompt needs observable details before suggesting diagnostics.",
        ),
        (
            "recent_changes",
            "What changed recently, and what have you already tried?",
            "Recent changes and attempted fixes narrow the likely causes.",
        ),
    ],
    "software_engineering": [
        (
            "tech_stack",
            "What stack, framework, language, or tool versions are involved?",
            "Technical prompts work better when the environment is explicit.",
        ),
        (
            "failure_mode",
            "What error message, unexpected behavior, or goal should the AI focus on?",
            "The model needs a concrete target for debugging or implementation.",
        ),
    ],
    "writing_communication": [
        (
            "audience",
            "Who is the audience, and what outcome should the message achieve?",
            "Audience and desired outcome shape tone, structure, and wording.",
        ),
        (
            "constraints",
            "Are there details, sensitivities, or phrases that must be included or avoided?",
            "Communication prompts need context boundaries to avoid awkward drafts.",
        ),
    ],
    "learning_research": [
        (
            "current_level",
            "What do you already know, and what level should the explanation target?",
            "The prompt should match the user's starting point.",
        ),
        (
            "output_goal",
            "Do you want a summary, study plan, comparison, examples, or sources?",
            "The output format determines how the research prompt should be framed.",
        ),
    ],
    "business_strategy": [
        (
            "business_goal",
            "What decision or business outcome should the answer support?",
            "Business prompts need a clear decision target.",
        ),
        (
            "constraints",
            "What constraints, market, audience, or timeline matter?",
            "Constraints keep the answer from becoming generic.",
        ),
    ],
    "health_wellness": [
        (
            "situation",
            "What is the situation, and what kind of information do you need?",
            "Health prompts need context and a clear non-diagnostic boundary.",
        ),
        (
            "boundaries",
            "Should the answer stay educational, suggest questions for a professional, or compare options?",
            "The prompt should avoid pretending to replace professional care.",
        ),
    ],
    "legal_financial": [
        (
            "jurisdiction_or_context",
            "What location, document, account, or context is involved?",
            "Legal and financial prompts depend heavily on context.",
        ),
        (
            "decision_needed",
            "What decision do you need help preparing for?",
            "The prompt should support decision preparation without overclaiming.",
        ),
    ],
    "creative_media": [
        (
            "creative_goal",
            "What should the final creative output be?",
            "Creative prompts need a concrete deliverable.",
        ),
        (
            "style_constraints",
            "What style, audience, channel, or references should guide it?",
            "Style and audience make creative output less generic.",
        ),
    ],
    "general_problem_solving": [
        (
            "goal",
            "What would a useful final answer help you decide or do?",
            "The prompt needs a clear success condition.",
        ),
        (
            "context",
            "What context, constraints, or failed attempts should the AI know?",
            "Context and constraints prevent generic answers.",
        ),
    ],
}


def generate_questions(
    problem: str,
    classification: ClassificationResponse,
    profile_traits: list[Any] | None = None,
) -> list[ClarifyingQuestion]:
    seeds = DOMAIN_QUESTIONS.get(
        classification.domain,
        DOMAIN_QUESTIONS["general_problem_solving"],
    )

    questions = [
        ClarifyingQuestion(id=question_id, question=question, reason=reason)
        for question_id, question, reason in seeds
    ]

    lowered = problem.lower()
    if _needs_success_criteria(lowered, profile_traits):
        questions.append(
            ClarifyingQuestion(
                id="success_criteria",
                question="What would make the final answer successful for you?",
                reason="A clear success condition helps the prompt avoid generic advice.",
            )
        )

    if _needs_constraints(lowered, questions, profile_traits):
        questions.append(
            ClarifyingQuestion(
                id="constraints",
                question="What constraints, requirements, or things to avoid should the AI respect?",
                reason="Explicit constraints keep the refined prompt grounded in the real situation.",
            )
        )

    if _needs_audience(classification.domain, lowered):
        questions.append(
            ClarifyingQuestion(
                id="audience",
                question="Who is the answer for, and what level of familiarity should it assume?",
                reason="Audience changes tone, depth, examples, and vocabulary.",
                required=False,
            )
        )

    if _strong_trait(profile_traits, "source_expectation"):
        questions.append(
            ClarifyingQuestion(
                id="source_boundary",
                question="Should the answer use general knowledge, cite sources when needed, or stick to official sources?",
                reason="Your profile suggests source expectations may shape answer quality.",
                required=False,
            )
        )

    if classification.risk_level in {"medium", "high"}:
        questions.append(
            ClarifyingQuestion(
                id="safety_boundary",
                question="Are there safety, legal, financial, or professional boundaries the answer must respect?",
                reason="Higher-risk prompts should make boundaries explicit.",
                required=classification.risk_level == "high",
            )
        )

    return _dedupe_questions(questions)


def _needs_success_criteria(problem: str, profile_traits: list[Any] | None) -> bool:
    has_goal = any(
        term in problem
        for term in {
            "so that",
            "goal",
            "success",
            "decide",
            "choose",
            "fix",
            "build",
            "write",
            "compare",
        }
    )
    return not has_goal or _weak_trait(profile_traits, "goal_clarity")


def _needs_constraints(
    problem: str,
    questions: list[ClarifyingQuestion],
    profile_traits: list[Any] | None,
) -> bool:
    if any(question.id == "constraints" for question in questions):
        return False
    has_constraints = any(
        term in problem
        for term in {"must", "only", "avoid", "without", "budget", "deadline", "using"}
    )
    return not has_constraints or _weak_trait(profile_traits, "constraint_specificity")


def _needs_audience(domain: str, problem: str) -> bool:
    if domain not in {
        "writing_communication",
        "learning_research",
        "business_strategy",
        "creative_media",
    }:
        return False
    return not any(term in problem for term in {"audience", "reader", "client", "team", "student"})


def _dedupe_questions(questions: list[ClarifyingQuestion]) -> list[ClarifyingQuestion]:
    seen: set[str] = set()
    deduped: list[ClarifyingQuestion] = []
    for question in questions:
        if question.id in seen:
            continue
        seen.add(question.id)
        deduped.append(question)
    return deduped


def _weak_trait(profile_traits: list[Any] | None, trait_key: str) -> bool:
    trait = _find_trait(profile_traits, trait_key)
    if not trait:
        return False
    return _trait_float(trait, "score") < 0.45 and _trait_float(trait, "confidence") >= 0.35


def _strong_trait(profile_traits: list[Any] | None, trait_key: str) -> bool:
    trait = _find_trait(profile_traits, trait_key)
    if not trait:
        return False
    return _trait_float(trait, "score") >= 0.7 and _trait_float(trait, "confidence") >= 0.45


def _find_trait(profile_traits: list[Any] | None, trait_key: str) -> Any | None:
    for trait in profile_traits or []:
        value = trait.get("trait_key") if isinstance(trait, dict) else getattr(trait, "trait_key", None)
        if value == trait_key:
            return trait
    return None


def _trait_float(trait: Any, key: str) -> float:
    value = trait.get(key) if isinstance(trait, dict) else getattr(trait, key, 0.0)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
