from app.models import ProblemSession, PromptVariant
from app.schemas import PromptSettings


PROMPT_STRATEGIES = [
    "diagnostic",
    "beginner_step_by_step",
    "expert_consultant",
    "safety_first",
    "comparison",
    "questions_first",
]


def _settings_lines(settings: PromptSettings) -> list[str]:
    return [
        f"- Depth: {settings.length}",
        f"- Skill level: {settings.skill_level}",
        f"- Tone: {settings.tone}",
        f"- Output format: {settings.format}",
        f"- Risk posture: {settings.risk}",
        f"- Source preference: {settings.sources}",
    ]


def _context_lines(session: ProblemSession) -> list[str]:
    lines = [f"Problem: {session.raw_input}"]
    if session.detected_domain:
        lines.append(f"Detected domain: {session.detected_domain}")
    if session.detected_intent:
        lines.append(f"Detected intent: {session.detected_intent}")
    if session.risk_level:
        lines.append(f"Risk level: {session.risk_level}")
    if session.answers:
        lines.append("User answers:")
        lines.extend(
            f"- {question_id}: {answer}"
            for question_id, answer in sorted(session.answers.items())
        )
    return lines


def _format_instruction(settings: PromptSettings) -> str:
    formats = {
        "checklist": "Use a concise checklist with clear pass/fail checks.",
        "guide": "Use a structured guide with headings and practical steps.",
        "table": "Use tables for comparisons, causes, evidence, and next actions.",
        "conversation": "Use a conversational coaching style with short turns.",
        "plan": "Use a staged plan with priorities, sequence, and decision points.",
    }
    return formats[settings.format]


def _length_instruction(settings: PromptSettings) -> str:
    return {
        "short": "Keep the answer compact and focus on the highest-leverage details.",
        "medium": "Give enough detail to be actionable without becoming exhaustive.",
        "deep": "Go deep: include reasoning, alternatives, edge cases, and escalation criteria.",
    }[settings.length]


def choose_prompt_strategies(
    session: ProblemSession,
    settings: PromptSettings,
    needs_clarification: bool,
) -> list[str]:
    strategies: list[str] = []

    if session.risk_level in {"medium", "high"} or settings.risk == "safe_only":
        strategies.append("safety_first")
    if needs_clarification:
        strategies.append("questions_first")
    if session.detected_intent == "compare":
        strategies.append("comparison")
    if session.detected_intent == "troubleshoot":
        strategies.append("diagnostic")
    if settings.skill_level == "expert":
        strategies.append("expert_consultant")
    else:
        strategies.append("beginner_step_by_step")

    for fallback in ("diagnostic", "expert_consultant", "comparison", "questions_first"):
        strategies.append(fallback)

    unique: list[str] = []
    for strategy in strategies:
        if strategy not in unique:
            unique.append(strategy)
        if len(unique) == 3:
            return unique
    return unique


def _prompt_for_strategy(
    strategy: str,
    context: str,
    settings: PromptSettings,
    settings_block: str,
) -> tuple[str, str]:
    format_instruction = _format_instruction(settings)
    length_instruction = _length_instruction(settings)

    templates = {
        "diagnostic": (
            "Diagnostic Clarifier",
            (
                "You are a careful diagnostic assistant. Use the context below to identify likely causes, "
                "ask only the most useful missing questions, and provide a prioritized next-step plan.\n\n"
                f"{context}\n\nUser preferences:\n{settings_block}\n\n"
                f"{format_instruction} {length_instruction} "
                "Respond with: likely causes, evidence to collect, safest first actions, and when to escalate."
            ),
        ),
        "beginner_step_by_step": (
            "Step-by-Step Guide",
            (
                "Turn this messy request into a clear, beginner-friendly prompt for an AI assistant. "
                "The final answer should be practical, ordered, and easy to follow.\n\n"
                f"{context}\n\nUser preferences:\n{settings_block}\n\n"
                f"{format_instruction} {length_instruction} "
                "Ask for missing context if needed, then produce a checklist-style plan with assumptions called out."
            ),
        ),
        "expert_consultant": (
            "Expert Consultant Brief",
            (
                "Act as an expert consultant. Analyze the request, identify constraints and risks, "
                "and produce a high-signal answer that explains tradeoffs and recommended action.\n\n"
                f"{context}\n\nUser preferences:\n{settings_block}\n\n"
                f"{format_instruction} {length_instruction} "
                "Structure the response as: recommendation, rationale, alternatives, risks, and next actions."
            ),
        ),
        "safety_first": (
            "Safety-First Plan",
            (
                "You are a safety-first assistant. Start by identifying what could go wrong, what the user "
                "should not attempt, and when a qualified professional is needed. Then provide conservative, "
                "reversible next steps.\n\n"
                f"{context}\n\nUser preferences:\n{settings_block}\n\n"
                f"{format_instruction} {length_instruction} "
                "Do not give hazardous instructions. Include stop conditions, protective checks, and escalation triggers."
            ),
        ),
        "comparison": (
            "Comparison Matrix",
            (
                "Help the user compare viable options. Identify criteria, tradeoffs, risks, missing evidence, "
                "and a recommended choice based on the stated constraints.\n\n"
                f"{context}\n\nUser preferences:\n{settings_block}\n\n"
                f"{format_instruction} {length_instruction} "
                "Use a comparison matrix, then summarize the best option and the condition that would change it."
            ),
        ),
        "questions_first": (
            "Questions-First Intake",
            (
                "Before answering, gather the missing context that would most improve answer quality. "
                "Ask focused questions, explain why each matters, and then provide a provisional path if the "
                "user cannot answer yet.\n\n"
                f"{context}\n\nUser preferences:\n{settings_block}\n\n"
                f"{format_instruction} {length_instruction} "
                "Separate required questions from optional details, then give a cautious preliminary plan."
            ),
        ),
    }
    return templates[strategy]


def generate_prompt_variants(
    session: ProblemSession,
    settings: PromptSettings,
    strategies: list[str] | None = None,
) -> list[PromptVariant]:
    context = "\n".join(_context_lines(session))
    settings_block = "\n".join(_settings_lines(settings))
    selected_strategies = strategies or ["diagnostic", "beginner_step_by_step", "expert_consultant"]
    prompts: list[PromptVariant] = []
    for strategy in selected_strategies:
        title, prompt_text = _prompt_for_strategy(strategy, context, settings, settings_block)
        prompts.append(
            PromptVariant(
                session_id=session.id,
                title=title,
                strategy=strategy,
                prompt_text=prompt_text,
            )
        )

    if settings.risk == "safe_only" or session.risk_level == "high":
        for prompt in prompts:
            prompt.recommendation_label = "recommended" if prompt.strategy == "safety_first" else "candidate"
    elif prompts:
        prompts[0].recommendation_label = "recommended"

    return prompts
