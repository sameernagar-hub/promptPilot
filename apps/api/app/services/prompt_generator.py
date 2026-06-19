from app.models import ProblemSession, PromptVariant
from app.schemas import PromptSettings


PROMPT_STRATEGIES = [
    "recommended_prompt",
    "diagnostic",
    "beginner_step_by_step",
    "expert_consultant",
    "safety_first",
    "comparison",
    "questions_first",
]


def _settings_lines(settings: PromptSettings) -> list[str]:
    return [
        f"- Target platform: {settings.target_platform}",
        f"- Detail level: {settings.detail_level}",
        f"- Depth: {settings.length}",
        f"- Skill level: {settings.skill_level}",
        f"- Tone: {settings.tone}",
        f"- Formality: {settings.formality}",
        f"- Temperature: {settings.temperature}",
        f"- Reasoning style: {settings.reasoning_style}",
        f"- Source strictness: {settings.source_strictness}",
        f"- Interaction mode: {settings.interaction_mode}",
        f"- Output format: {settings.format}",
        f"- Risk posture: {settings.risk}",
        f"- Source preference: {settings.sources}",
    ]


DOMAIN_ROLES = {
    "bicycle_repair": "a mechanical engineer and bicycle repair specialist",
    "automotive_repair": "an experienced automotive diagnostic technician",
    "home_repair": "a careful home repair diagnostician",
    "software_engineering": "a senior software engineer",
    "writing_communication": "a communication strategist and editor",
    "learning_research": "a patient research coach",
    "business_strategy": "a pragmatic business strategy advisor",
    "health_wellness": "a careful health information assistant",
    "legal_financial": "a cautious legal and financial research assistant",
    "creative_media": "a creative director",
    "general_problem_solving": "a practical problem-solving coach",
}


PLATFORM_BEHAVIOR = {
    "codex": (
        "Optimize for Codex. Emphasize repository context, relevant files, constraints, "
        "implementation steps, verification commands, and expected code-change behavior."
    ),
    "claude": (
        "Optimize for Claude. Support long-context analysis, careful structure, nuanced tradeoffs, "
        "and a deliberate answer with clearly labeled assumptions."
    ),
    "chatgpt": (
        "Optimize for ChatGPT. Keep the prompt portable, explicit, general-purpose, and easy to reuse."
    ),
    "gemini": (
        "Optimize for Gemini. Mention multimodal inputs, broad research context, and source comparison when relevant."
    ),
    "cursor": (
        "Optimize for Cursor. Emphasize files, editor context, incremental code edits, tests, and concise implementation notes."
    ),
    "grok": (
        "Optimize for Grok. Keep the prompt direct, contrastive, current-context aware, and easy to iterate."
    ),
    "perplexity": (
        "Optimize for Perplexity. Emphasize source-backed research, citations, evidence boundaries, and comparison of claims."
    ),
    "copilot": (
        "Optimize for Copilot. Emphasize concise workflow context, document or code context, and practical next actions."
    ),
    "generic": (
        "Optimize for a generic AI assistant. Avoid provider-specific features or assumptions."
    ),
    "other": (
        "Optimize for a generic AI assistant. Avoid provider-specific features or assumptions."
    ),
}


def _context_lines(session: ProblemSession) -> list[str]:
    lines = [f"User request context: {session.raw_input}"]
    if session.display_name or session.primary_ai_platform:
        lines.append(
            "Session profile: "
            f"{session.display_name or 'User'} wants help with "
            f"{(session.primary_ai_platform or 'an AI assistant').replace('_', ' ')}."
        )
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
    skipped = [
        question.question_key
        for question in session.question_rows
        if question.answer_state == "skipped"
    ]
    if skipped:
        lines.append("Skipped context:")
        lines.extend(f"- {question_id}" for question_id in sorted(skipped))
    lines.append("Assumptions:")
    lines.extend(_assumption_lines(session))
    lines.append("Constraints:")
    lines.extend(_constraint_lines(session))
    return lines


def _domain_label(session: ProblemSession) -> str:
    classification = session.classification or {}
    domain = session.detected_domain or classification.get("domain") or "general_problem_solving"
    confirmed = classification.get("confirmed_domain")
    source = classification.get("domain_source", "detected")
    label = str(confirmed or domain).replace("_", " ")
    if source in {"user_confirmed", "user_corrected"}:
        return f"{label} (confirmed)"
    return label


def _role_for_session(session: ProblemSession) -> str:
    classification = session.classification or {}
    domain = str(session.detected_domain or classification.get("domain") or "general_problem_solving")
    return DOMAIN_ROLES.get(domain, f"a domain expert in {domain.replace('_', ' ')}")


def _question_lines(session: ProblemSession) -> list[str]:
    unanswered = [
        question
        for question in session.question_rows
        if question.required and question.answer_state == "unanswered"
    ]
    if not unanswered:
        return ["- Ask one short follow-up only if a critical detail is missing."]
    return [
        f"- {question.question}"
        for question in unanswered[:4]
    ]


def _known_detail_lines(session: ProblemSession) -> list[str]:
    answered = [
        question
        for question in session.question_rows
        if question.answer_state == "answered" and question.answer
    ]
    if not answered:
        return ["- No extra details provided yet."]
    return [
        f"- {question.question_key.replace('_', ' ')}: {question.answer}"
        for question in sorted(answered, key=lambda item: item.question_key)
    ]


def _assumption_lines(session: ProblemSession) -> list[str]:
    assumptions = [
        f"- {question.question_key.replace('_', ' ')} was skipped or left unspecified; do not overfit the answer to unstated details."
        for question in session.question_rows
        if question.required and question.answer_state in {"skipped", "unanswered"}
    ]
    if not assumptions:
        return ["- No major assumptions beyond the user's stated details."]
    return assumptions


def _constraint_lines(session: ProblemSession) -> list[str]:
    constraints = []
    if session.risk_level in {"medium", "high"}:
        constraints.append("- Treat safety, reversibility, and escalation criteria as hard constraints.")
    if session.detected_domain:
        constraints.append(f"- Stay within the {session.detected_domain.replace('_', ' ')} domain unless the user corrects it.")
    return constraints or ["- Respect any constraints the user provides in the known details."]


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
    detail = {
        "concise": "Use concise detail: preserve only the highest-value context and instructions.",
        "balanced": "Use balanced detail: include enough structure to be actionable without becoming heavy.",
        "exhaustive": "Use exhaustive detail: include edge cases, alternatives, validation criteria, and escalation paths.",
    }[settings.detail_level]
    legacy_depth = {
        "short": "Keep the answer compact and focus on the highest-leverage details.",
        "medium": "Give enough detail to be actionable without becoming exhaustive.",
        "deep": "Go deep: include reasoning, alternatives, edge cases, and escalation criteria.",
    }[settings.length]
    return f"{detail} {legacy_depth}"


def _temperature_instruction(session: ProblemSession, settings: PromptSettings) -> str:
    if settings.temperature == "precise":
        return "Use low creativity and prioritize precise, verifiable, non-speculative guidance."
    if settings.temperature == "creative":
        return "Use creative exploration while clearly separating ideas from confirmed facts."
    if settings.risk == "safe_only" or session.risk_level in {"medium", "high"}:
        return "Use low creativity and prioritize accuracy, caution, and verifiable next steps."
    if session.detected_domain == "creative_media" or settings.risk == "advanced":
        return "Use balanced creativity: explore options while keeping the answer usable."
    return "Use balanced creativity and avoid making up missing facts."


def _source_boundary(settings: PromptSettings) -> str:
    if settings.source_strictness == "official_only":
        return "Use official sources only when source-backed claims are needed; say when verification is required."
    if settings.source_strictness == "evidence_first":
        return "Lead with evidence, cite or describe support for important claims, and separate inference from fact."
    if settings.source_strictness == "cite_when_needed":
        return "Cite sources for claims that are specific, time-sensitive, factual, legal, medical, financial, or technical."
    if settings.sources == "official_docs":
        return "Prefer official sources and say when a claim needs verification."
    if settings.sources == "web":
        return "Use sources when useful and separate sourced claims from assumptions."
    return "Do not invent citations; state uncertainty when facts are missing."


def _platform_label(platform: str) -> str:
    labels = {
        "codex": "Codex",
        "claude": "Claude",
        "chatgpt": "ChatGPT",
        "gemini": "Gemini",
        "cursor": "Cursor",
        "grok": "Grok",
        "perplexity": "Perplexity",
        "copilot": "Copilot",
        "generic": "Generic",
        "other": "Other AI",
    }
    return labels.get(platform, platform.replace("_", " ").title())


def _platform_behavior(settings: PromptSettings) -> str:
    return PLATFORM_BEHAVIOR.get(settings.target_platform, PLATFORM_BEHAVIOR["generic"])


def _reasoning_instruction(settings: PromptSettings) -> str:
    return {
        "direct_answer": "Reasoning style: give the answer first, then only the rationale needed to support it.",
        "step_by_step": "Reasoning style: use a step-by-step structure with clear sequencing and checkpoints.",
        "ask_first": "Reasoning style: ask critical missing questions before finalizing when context would materially change the answer.",
        "explore_options": "Reasoning style: explore viable options, tradeoffs, and decision criteria before recommending.",
    }[settings.reasoning_style]


def _interaction_instruction(settings: PromptSettings) -> str:
    return {
        "one_shot": "Interaction mode: produce the best complete one-shot answer with assumptions clearly stated.",
        "iterative": "Interaction mode: support a short iterative exchange and ask focused follow-ups only when they matter.",
        "agentic": "Interaction mode: act like an agent: plan, execute in safe steps, verify outcomes, and report what changed.",
    }[settings.interaction_mode]


def _formality_instruction(settings: PromptSettings) -> str:
    return {
        "casual": "Use casual wording while staying clear and respectful.",
        "neutral": "Use neutral wording that is professional but not stiff.",
        "formal": "Use formal, polished wording suitable for professional use.",
    }[settings.formality]


def choose_prompt_strategies(
    session: ProblemSession,
    settings: PromptSettings,
    needs_clarification: bool,
) -> list[str]:
    strategies: list[str] = ["recommended_prompt"]

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
    session: ProblemSession,
    settings: PromptSettings,
    context: str,
    settings_block: str,
) -> tuple[str, str]:
    format_instruction = _format_instruction(settings)
    length_instruction = _length_instruction(settings)
    role = _role_for_session(session)
    domain = _domain_label(session)
    questions = "\n".join(_question_lines(session))
    known_details = "\n".join(_known_detail_lines(session))
    assumptions = "\n".join(_assumption_lines(session))
    constraints = "\n".join(_constraint_lines(session))
    platform_label = _platform_label(settings.target_platform)
    platform_behavior = _platform_behavior(settings)
    reasoning_instruction = _reasoning_instruction(settings)
    interaction_instruction = _interaction_instruction(settings)
    formality_instruction = _formality_instruction(settings)
    recommended_title = (
        "Recommended Prompt"
        if settings.target_platform == "generic"
        else f"{platform_label}-Ready Prompt"
    )

    templates = {
        "recommended_prompt": (
            recommended_title,
            (
                f"Role: You are {role}.\n"
                f"Task: Help the user with this request using practical, domain-specific judgment.\n"
                f"Target platform: {platform_label}.\n"
                f"Platform behavior: {platform_behavior}\n"
                f"Context: {session.raw_input}\n"
                f"Domain: {domain}\n"
                f"Intent: {(session.detected_intent or 'clarify and solve').replace('_', ' ')}\n"
                f"Risk level: {session.risk_level or 'low'}\n\n"
                "Known user details:\n"
                f"{known_details}\n\n"
                "Constraints:\n"
                f"{constraints}\n\n"
                "Audience: Match the user's stated audience if provided; otherwise assume a capable non-expert.\n"
                f"Tone: {settings.tone.replace('_', ' ')}.\n"
                f"Formality: {settings.formality}. {formality_instruction}\n"
                f"Detail level: {settings.detail_level} for a {settings.skill_level} user.\n"
                f"Temperature or creativity guidance: {_temperature_instruction(session, settings)}\n"
                f"{reasoning_instruction}\n"
                f"{interaction_instruction}\n"
                f"Output format: {settings.format}. {_format_instruction(settings)}\n"
                "Success criteria: The answer should be specific, actionable, bounded by the known facts, and clear about what would change the recommendation.\n\n"
                "Assumptions:\n"
                f"{assumptions}\n\n"
                "Follow-up behavior:\n"
                f"{questions}\n\n"
                f"Safety or source boundaries: {_source_boundary(settings)}\n\n"
                "Produce the final answer with this structure:\n"
                "1. Best current interpretation\n"
                "2. Recommended next actions\n"
                "3. Risks, stop conditions, or escalation points\n"
                "4. Assumptions and missing context\n"
                "5. A concise follow-up question only if it would materially improve the answer\n\n"
                f"User preferences:\n{settings_block}\n\n"
                f"{length_instruction}"
            ),
        ),
        "diagnostic": (
            "Diagnostic Clarifier",
            (
                "You are a careful diagnostic assistant. Use the context below to identify likely causes, "
                "ask only the most useful missing questions, and provide a prioritized next-step plan.\n\n"
                f"{context}\n\nUser preferences:\n{settings_block}\n\n"
                f"Target platform behavior:\n{platform_behavior}\n\n"
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
                f"Assumptions to carry forward:\n{assumptions}\n\n"
                f"Target platform behavior:\n{platform_behavior}\n\n"
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
                f"Assumptions to carry forward:\n{assumptions}\n\n"
                f"Target platform behavior:\n{platform_behavior}\n\n"
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
                f"Target platform behavior:\n{platform_behavior}\n\n"
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
                f"Target platform behavior:\n{platform_behavior}\n\n"
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
                f"Target platform behavior:\n{platform_behavior}\n\n"
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
        title, prompt_text = _prompt_for_strategy(strategy, session, settings, context, settings_block)
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
