from app.models import ProblemSession, PromptVariant
from app.schemas import KnowledgeRetrievalContext, PromptSettings
from app.services.domain_capabilities import (
    effective_interaction_mode,
    effective_source_strictness,
    platform_behavior,
)
from app.services.knowledge_support import knowledge_context_to_prompt_lines


PROMPT_STRATEGIES = [
    "recommended_prompt",
    "builder_plan",
    "diagnostic",
    "learning_explainer",
    "beginner_step_by_step",
    "expert_consultant",
    "safety_first",
    "comparison",
    "questions_first",
]


def _settings_lines(settings: PromptSettings, session: ProblemSession) -> list[str]:
    source_strictness = effective_source_strictness(
        settings,
        _domain_for_session(session),
        raw_input=session.raw_input,
        intent=_intent_for_session(session),
    )
    interaction_mode = effective_interaction_mode(settings, _domain_for_session(session))
    return [
        f"- Target platform: {settings.target_platform}",
        f"- Detail level: {settings.detail_level}",
        f"- Depth: {settings.length}",
        f"- Skill level: {settings.skill_level}",
        f"- Tone: {settings.tone}",
        f"- Formality: {settings.formality}",
        f"- Temperature: {settings.temperature}",
        f"- Reasoning style: {settings.reasoning_style}",
        f"- Source strictness: {source_strictness}",
        f"- Interaction mode: {interaction_mode}",
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
    "hobby_project": "a hands-on hobby project guide",
    "general_problem_solving": "a practical problem-solving coach",
}

BUILD_ROLES = {
    "bicycle_repair": "a hands-on bicycle maintenance guide",
    "automotive_repair": "a careful automotive project planning guide",
    "home_repair": "a practical home project guide",
    "software_engineering": "a senior software implementation guide",
    "creative_media": "a creative production guide",
    "hobby_project": "a hands-on hobby project guide",
    "general_problem_solving": "a practical how-to guide",
}

LEARNING_ROLES = {
    "software_engineering": "a patient technical educator",
    "health_wellness": "a careful health education assistant",
    "legal_financial": "a cautious legal and financial research educator",
    "hobby_project": "a patient hands-on learning guide",
    "general_problem_solving": "a patient explainer",
}

DECISION_ROLES = {
    "business_strategy": "a pragmatic decision advisor",
    "legal_financial": "a cautious decision-preparation assistant",
    "hobby_project": "a practical project tradeoff advisor",
    "general_problem_solving": "a practical decision coach",
}

INTENT_STRATEGIES = {
    "build": "builder_plan",
    "troubleshoot": "diagnostic",
    "learn": "learning_explainer",
    "compare": "comparison",
    "research": "learning_explainer",
    "plan": "builder_plan",
}

INTENT_RESPONSE_SHAPES = {
    "build": {
        "task": (
            "Help the user create or build the requested thing. Clarify scope, choose an appropriate "
            "approach or variant, then give an actionable build plan."
        ),
        "success": (
            "The answer should turn the creation goal into a practical plan with scope choices, "
            "requirements, materials, constraints, and safe next steps."
        ),
        "structure": [
            "1. Scope clarification",
            "2. Approach or variant choice",
            "3. Step-by-step plan",
            "4. Materials, tools, and requirements checklist",
            "5. Safety, constraints, and what would change the plan",
        ],
    },
    "troubleshoot": {
        "task": (
            "Help the user diagnose and fix the issue. Identify likely causes, collect evidence, "
            "prioritize safe first actions, and name escalation triggers."
        ),
        "success": (
            "The answer should narrow the problem safely, make evidence collection concrete, "
            "and separate low-risk actions from escalation conditions."
        ),
        "structure": [
            "1. Likely causes",
            "2. Evidence to collect",
            "3. Safest first actions",
            "4. Escalation triggers",
            "5. Assumptions and missing context",
        ],
    },
    "learn": {
        "task": (
            "Help the user understand the topic. Explain the core concept, use examples, prevent "
            "common misunderstandings, and suggest next learning steps."
        ),
        "success": (
            "The answer should make the concept understandable at the user's level, with examples "
            "and clear next steps instead of a generic overview."
        ),
        "structure": [
            "1. Core concept",
            "2. Examples",
            "3. Common confusions",
            "4. Suggested next steps",
            "5. A focused follow-up question if context would improve the explanation",
        ],
    },
    "compare": {
        "task": (
            "Help the user decide between options. Identify the options, compare tradeoffs, define "
            "recommendation criteria, and suggest a choice when enough context exists."
        ),
        "success": (
            "The answer should make the decision criteria explicit, compare tradeoffs fairly, and "
            "recommend a choice or identify the missing fact that would decide it."
        ),
        "structure": [
            "1. Options",
            "2. Tradeoffs",
            "3. Recommendation criteria",
            "4. Suggested choice",
            "5. What would change the recommendation",
        ],
    },
}


AGENT_TRACK_LABELS = {
    "fix": "Fix",
    "build": "Build",
    "learn": "Learn",
    "write": "Write",
    "compare": "Compare",
    "research": "Research",
}


def _context_lines(
    session: ProblemSession,
    knowledge_context: KnowledgeRetrievalContext | None = None,
) -> list[str]:
    request_context = _clean_request_context(session.raw_input)
    lines = [f"User request context: {request_context}"]
    if session.display_name or session.primary_ai_platform:
        lines.append(
            "Session profile: "
            f"{session.display_name or 'User'} wants help with "
            f"{(session.primary_ai_platform or 'an AI assistant').replace('_', ' ')}."
        )
    agent_track = _agent_track_label(session)
    if agent_track:
        lines.append(f"Agent track: {agent_track}")
        lines.append(
            "Agent track rule: Use this as a workflow hint only; user settings, prompt content, safety rules, and profile preferences still take priority."
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
    if knowledge_context:
        lines.append("Retrieved pattern guidance:")
        lines.extend(knowledge_context_to_prompt_lines(knowledge_context))
        lines.append("Retrieval guardrails:")
        lines.append(
            "- The active request, confirmed domain, user settings, safety rules, and profile preferences take priority over retrieved patterns."
        )
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
    domain = _domain_for_session(session)
    intent = _intent_for_session(session)
    if intent == "build":
        return BUILD_ROLES.get(domain, f"a practical {domain.replace('_', ' ')} build guide")
    if intent == "learn":
        return LEARNING_ROLES.get(domain, f"a patient {domain.replace('_', ' ')} educator")
    if intent == "compare":
        return DECISION_ROLES.get(domain, f"a practical {domain.replace('_', ' ')} decision advisor")
    return DOMAIN_ROLES.get(domain, f"a domain expert in {domain.replace('_', ' ')}")


def _domain_for_session(session: ProblemSession) -> str:
    classification = session.classification or {}
    return str(session.detected_domain or classification.get("domain") or "general_problem_solving")


def _intent_for_session(session: ProblemSession) -> str:
    classification = session.classification or {}
    intent = str(session.detected_intent or classification.get("intent") or "clarify_and_plan")
    aliases = {
        "create": "build",
        "diagnose": "troubleshoot",
        "fix": "troubleshoot",
        "explain": "learn",
        "decide": "compare",
    }
    return aliases.get(intent, intent)


def _response_shape_for_session(session: ProblemSession) -> dict[str, list[str] | str]:
    intent = _intent_for_session(session)
    if intent in INTENT_RESPONSE_SHAPES:
        return INTENT_RESPONSE_SHAPES[intent]
    if intent in {"write", "research"}:
        return INTENT_RESPONSE_SHAPES["learn"]
    if intent == "plan":
        return INTENT_RESPONSE_SHAPES["build"]
    return {
        "task": (
            "Help the user clarify the request, choose a useful approach, and produce practical next steps."
        ),
        "success": (
            "The answer should be specific, actionable, bounded by known facts, and clear about missing context."
        ),
        "structure": [
            "1. Best current interpretation",
            "2. Recommended approach",
            "3. Practical next steps",
            "4. Constraints and assumptions",
            "5. A concise follow-up question only if it would materially improve the answer",
        ],
    }


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


def _source_boundary(settings: PromptSettings, session: ProblemSession) -> str:
    source_strictness = effective_source_strictness(
        settings,
        _domain_for_session(session),
        raw_input=session.raw_input,
        intent=_intent_for_session(session),
    )
    if source_strictness == "official_only":
        return "Use official sources only when source-backed claims are needed; say when verification is required."
    if source_strictness == "evidence_first":
        return "Lead with evidence, cite or describe support for important claims, and separate inference from fact."
    if source_strictness == "cite_when_needed":
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


def _platform_behavior(settings: PromptSettings, session: ProblemSession) -> str:
    return platform_behavior(settings.target_platform, _domain_for_session(session))


def _clean_request_context(raw_input: str) -> str:
    cleaned = raw_input.strip()
    if cleaned.lower().startswith("problem:"):
        return cleaned.split(":", 1)[1].strip()
    return cleaned


def _agent_track_label(session: ProblemSession) -> str | None:
    value = (session.session_metadata or {}).get("agent_track")
    return AGENT_TRACK_LABELS.get(str(value)) if value else None


def _reasoning_instruction(settings: PromptSettings) -> str:
    return {
        "direct_answer": "Reasoning style: give the answer first, then only the rationale needed to support it.",
        "step_by_step": "Reasoning style: use a step-by-step structure with clear sequencing and checkpoints.",
        "ask_first": "Reasoning style: ask critical missing questions before finalizing when context would materially change the answer.",
        "explore_options": "Reasoning style: explore viable options, tradeoffs, and decision criteria before recommending.",
    }[settings.reasoning_style]


def _interaction_instruction(settings: PromptSettings, session: ProblemSession) -> str:
    interaction_mode = effective_interaction_mode(settings, _domain_for_session(session))
    return {
        "one_shot": "Interaction mode: produce the best complete one-shot answer with assumptions clearly stated.",
        "iterative": "Interaction mode: support a short iterative exchange and ask focused follow-ups only when they matter.",
        "agentic": "Interaction mode: act like an agent: plan, execute in safe steps, verify outcomes, and report what changed.",
        "guide": "Interaction mode: guide the user with a clear plan, practical checkpoints, and result checks they can do themselves.",
    }[interaction_mode]


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
    intent = _intent_for_session(session)
    intent_strategy = INTENT_STRATEGIES.get(intent)

    if intent_strategy:
        strategies.append(intent_strategy)

    if session.risk_level in {"medium", "high"} or settings.risk == "safe_only":
        strategies.append("safety_first")
    if needs_clarification:
        strategies.append("questions_first")
    if settings.skill_level == "expert":
        strategies.append("expert_consultant")
    else:
        strategies.append("beginner_step_by_step")

    fallback_by_intent = {
        "build": ("beginner_step_by_step", "expert_consultant", "questions_first"),
        "troubleshoot": ("diagnostic", "safety_first", "questions_first"),
        "learn": ("learning_explainer", "beginner_step_by_step", "expert_consultant"),
        "compare": ("comparison", "expert_consultant", "questions_first"),
    }
    for fallback in fallback_by_intent.get(
        intent,
        ("expert_consultant", "beginner_step_by_step", "questions_first"),
    ):
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
    knowledge_context: KnowledgeRetrievalContext | None = None,
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
    platform_behavior = _platform_behavior(settings, session)
    agent_track = _agent_track_label(session)
    agent_track_line = (
        f"Agent track: {agent_track} workflow hint only; user settings and request details still take priority.\n"
        if agent_track
        else ""
    )
    reasoning_instruction = _reasoning_instruction(settings)
    interaction_instruction = _interaction_instruction(settings, session)
    formality_instruction = _formality_instruction(settings)
    response_shape = _response_shape_for_session(session)
    response_structure = "\n".join(str(item) for item in response_shape["structure"])
    knowledge_lines = "\n".join(
        knowledge_context_to_prompt_lines(knowledge_context)
        if knowledge_context
        else ["- No licensed knowledge patterns were retrieved."]
    )
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
                f"Task: {response_shape['task']}\n"
                f"Target platform: {platform_label}.\n"
                f"Platform behavior: {platform_behavior}\n"
                f"{agent_track_line}"
                f"Context: {_clean_request_context(session.raw_input)}\n"
                f"Domain: {domain}\n"
                f"Intent: {(session.detected_intent or 'clarify and solve').replace('_', ' ')}\n"
                f"Risk level: {session.risk_level or 'low'}\n\n"
                "Known user details:\n"
                f"{known_details}\n\n"
                "Constraints:\n"
                f"{constraints}\n\n"
                "Knowledge support:\n"
                f"{knowledge_lines}\n"
                "- Treat retrieved patterns as optional structure only; user settings, confirmed domain, safety rules, and profile preferences override retrieval.\n\n"
                "Audience: Match the user's stated audience if provided; otherwise assume a capable non-expert.\n"
                f"Tone: {settings.tone.replace('_', ' ')}.\n"
                f"Formality: {settings.formality}. {formality_instruction}\n"
                f"Detail level: {settings.detail_level} for a {settings.skill_level} user.\n"
                f"Temperature or creativity guidance: {_temperature_instruction(session, settings)}\n"
                f"{reasoning_instruction}\n"
                f"{interaction_instruction}\n"
                f"Output format: {settings.format}. {_format_instruction(settings)}\n"
                f"Success criteria: {response_shape['success']}\n\n"
                "Assumptions:\n"
                f"{assumptions}\n\n"
                "Follow-up behavior:\n"
                f"{questions}\n\n"
                f"Safety or source boundaries: {_source_boundary(settings, session)}\n\n"
                "Produce the final answer with this structure:\n"
                f"{response_structure}\n\n"
                f"User preferences:\n{settings_block}\n\n"
                f"{length_instruction}"
            ),
        ),
        "builder_plan": (
            "Build Plan Prompt",
            (
                "Help the user create the requested project. Use a creation-first response shape: "
                "scope clarification, approach or variant choice, step-by-step plan, and a materials "
                "or requirements checklist. Use domain terminology and examples without turning the "
                "task into troubleshooting unless the user reports a failure.\n\n"
                f"{context}\n\nUser preferences:\n{settings_block}\n\n"
                f"Assumptions to carry forward:\n{assumptions}\n\n"
                f"Target platform behavior:\n{platform_behavior}\n\n"
                f"{format_instruction} {length_instruction} "
                "Include constraints, safety boundaries, and a short question only for missing details "
                "that would materially change the build plan."
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
        "learning_explainer": (
            "Learning Explainer",
            (
                "Help the user learn or understand the topic. Use the response shape: core concept, "
                "examples, common confusions, and suggested next steps. Match the user's current level "
                "and avoid turning the answer into a troubleshooting or build checklist unless requested.\n\n"
                f"{context}\n\nUser preferences:\n{settings_block}\n\n"
                f"Assumptions to carry forward:\n{assumptions}\n\n"
                f"Target platform behavior:\n{platform_behavior}\n\n"
                f"{format_instruction} {length_instruction} "
                "Use clear examples and name the next thing the user should try to check understanding."
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
    knowledge_context: KnowledgeRetrievalContext | None = None,
) -> list[PromptVariant]:
    context = "\n".join(_context_lines(session, knowledge_context))
    settings_block = "\n".join(_settings_lines(settings, session))
    selected_strategies = strategies or choose_prompt_strategies(
        session,
        settings,
        needs_clarification=False,
    )
    prompts: list[PromptVariant] = []
    for strategy in selected_strategies:
        title, prompt_text = _prompt_for_strategy(
            strategy,
            session,
            settings,
            context,
            settings_block,
            knowledge_context,
        )
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
