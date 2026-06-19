import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import get_settings
from app.models import PromptVariant
from app.schemas import ClassificationResponse, PromptSettings


SCORING_KEYS = [
    "input_to_contract_improvement",
    "contract_completeness",
    "assumption_handling",
    "domain_accuracy",
    "clarification_value",
    "platform_fit",
    "platform_fit_granularity",
    "backend_value_exposure",
    "safety_privacy_integrity",
    "user_actionability",
]

OLLAMA_SCORING_KEYS = [
    "input_to_contract_improvement",
    "contract_completeness",
    "assumption_handling",
    "domain_accuracy",
    "platform_fit",
    "safety_privacy_integrity",
    "user_actionability",
]

STRATEGY_PRIORITY = {
    "recommended_prompt": 0,
    "builder_plan": 1,
    "learning_explainer": 2,
    "comparison": 3,
    "safety_first": 4,
    "diagnostic": 5,
    "questions_first": 6,
    "beginner_step_by_step": 7,
    "expert_consultant": 8,
}

PLATFORM_TERMS = {
    "codex": {"codex", "repository", "repo", "files", "verification", "code-change"},
    "claude": {"claude", "long-context", "nuanced", "tradeoffs", "assumptions"},
    "chatgpt": {"chatgpt", "portable", "general-purpose", "reuse"},
    "gemini": {"gemini", "multimodal", "research", "sources"},
    "cursor": {"cursor", "editor", "files", "incremental", "tests"},
    "grok": {"grok", "direct", "current", "concise", "contrast"},
    "perplexity": {"perplexity", "sources", "research", "citations", "evidence"},
    "copilot": {"copilot", "microsoft", "document", "workflow", "productivity"},
    "generic": {"generic", "provider-specific", "assumptions"},
    "other": {"generic", "provider-specific", "assumptions"},
}

PLATFORM_BEHAVIOR_SUMMARIES = {
    "codex": "repo context, file constraints, implementation steps, and verification",
    "claude": "long-context structure, nuance, and labeled assumptions",
    "chatgpt": "portable, explicit, reusable instructions",
    "gemini": "broad research context, source comparison, and multimodal readiness",
    "cursor": "editor context, incremental edits, and test feedback",
    "grok": "direct framing, contrast, and concise iteration",
    "perplexity": "source-forward research, citations, and evidence boundaries",
    "copilot": "productivity workflow, document context, and concise execution",
    "generic": "provider-neutral instructions without platform assumptions",
    "other": "provider-neutral instructions without platform assumptions",
}

CONTRACT_MARKERS = {
    "role:",
    "task:",
    "context:",
    "domain:",
    "constraints:",
    "audience:",
    "tone:",
    "formality:",
    "detail level:",
    "output format:",
    "success criteria:",
    "assumptions:",
    "follow-up behavior:",
    "safety or source boundaries:",
}


def score_prompt_variants(
    problem: str,
    prompts: list[PromptVariant],
    settings: PromptSettings,
    risk_level: str | None = None,
    needs_clarification: bool = False,
    missing_context_count: int = 0,
    recommendation_notes: list[str] | None = None,
    classification: ClassificationResponse | dict[str, Any] | None = None,
    assumption_sources: list[dict[str, Any]] | None = None,
    profile_traits: list[dict[str, Any]] | None = None,
    session_profile: dict[str, Any] | None = None,
) -> list[PromptVariant]:
    classification_data = _classification_dict(classification)
    assumptions = assumption_sources or []
    traits = profile_traits or []
    notes = recommendation_notes or []
    scorer_metadata, model_scores = _ollama_scorer_result(
        problem=problem,
        prompts=prompts,
        settings=settings,
        classification=classification_data,
        assumption_sources=assumptions,
    )
    scored: list[PromptVariant] = []

    for prompt in prompts:
        deterministic_breakdown = _score_prompt(
            problem,
            prompt,
            settings,
            classification=classification_data,
            risk_level=risk_level,
            needs_clarification=needs_clarification,
            missing_context_count=missing_context_count,
        )
        model_breakdown = (
            model_scores.get(prompt.strategy)
            or model_scores.get(prompt.id)
            or model_scores.get(prompt.title)
        )
        prompt.score_breakdown = _blend_score_breakdowns(
            deterministic_breakdown,
            model_breakdown,
        )
        prompt.score_total = round(
            sum(prompt.score_breakdown.values()) / len(prompt.score_breakdown),
            2,
        )
        prompt_scorer_metadata = {
            **scorer_metadata,
            "model_scores_used": bool(model_breakdown),
            "model_score_key": prompt.strategy if model_breakdown else None,
        }
        prompt.explanation = _explanation_for_prompt(
            prompt,
            settings,
            missing_context_count=missing_context_count,
            recommendation_notes=notes,
            session_profile=session_profile or {},
        )
        prompt.score_metadata = _score_metadata_for_prompt(
            problem=problem,
            prompt=prompt,
            settings=settings,
            classification=classification_data,
            assumption_sources=assumptions,
            profile_traits=traits,
            session_profile=session_profile or {},
            scorer_metadata=prompt_scorer_metadata,
            recommendation_notes=notes,
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
        if prompt.recommendation_label == "recommended":
            prompt.score_metadata["recommendation_summary"] = (
                "Best current fit for the selected platform and available context."
            )
            prompt.score_metadata["recommended_actions"] = _recommended_actions(
                prompt,
                settings,
                prompt.score_metadata.get("assumption_notes") or [],
            )
    return scored


def _score_prompt(
    problem: str,
    prompt: PromptVariant,
    settings: PromptSettings,
    classification: dict[str, Any],
    risk_level: str | None = None,
    needs_clarification: bool = False,
    missing_context_count: int = 0,
) -> dict[str, float]:
    text = prompt.prompt_text.lower()
    problem_terms = {term.strip(".,:;!?()[]") for term in problem.lower().split()}
    matched_terms = [term for term in problem_terms if len(term) > 3 and term in text]
    is_recommended = prompt.strategy == "recommended_prompt"
    is_questions_first = prompt.strategy == "questions_first"
    is_safety_first = prompt.strategy == "safety_first"
    risk_bonus = risk_level in {"medium", "high"} or settings.risk == "safe_only"
    domain = str(classification.get("domain") or classification.get("primary_domain") or "")
    domain_text = domain.replace("_", " ")

    platform_fit = _platform_fit_score(text, settings.target_platform)
    scores = {
        "input_to_contract_improvement": min(
            0.96,
            0.62 + (0.03 * len(matched_terms)) + (0.12 if is_recommended else 0.04),
        ),
        "contract_completeness": _contract_completeness_score(text),
        "assumption_handling": _assumption_handling_score(text, missing_context_count),
        "domain_accuracy": min(
            0.95,
            0.64
            + (0.03 * len(matched_terms))
            + (0.1 if domain and (domain in text or domain_text in text) else 0),
        ),
        "clarification_value": 0.92
        if is_questions_first and needs_clarification
        else (0.86 if missing_context_count else 0.78),
        "platform_fit": platform_fit,
        "platform_fit_granularity": max(
            platform_fit,
            0.86 if "platform behavior:" in text or "target platform:" in text else 0.66,
        ),
        "backend_value_exposure": 0.88 if is_recommended else 0.76,
        "safety_privacy_integrity": 0.96
        if is_safety_first or risk_bonus
        else (0.86 if "safety" in text or "source boundaries" in text else 0.74),
        "user_actionability": 0.94
        if "recommended next actions" in text
        or "step-by-step plan" in text
        or "materials" in text
        or "next actions" in text
        else (0.86 if "plan" in text or "checklist" in text else 0.72),
    }
    if is_recommended:
        scores["contract_completeness"] = max(scores["contract_completeness"], 0.9)
        scores["domain_accuracy"] = max(scores["domain_accuracy"], 0.88)
        scores["platform_fit"] = max(scores["platform_fit"], 0.9)
    if missing_context_count:
        penalty = min(0.1, missing_context_count * 0.025)
        scores["input_to_contract_improvement"] = max(
            0.58,
            scores["input_to_contract_improvement"] - penalty,
        )
        scores["domain_accuracy"] = max(0.58, scores["domain_accuracy"] - (penalty / 2))
    return {key: round(scores[key], 2) for key in SCORING_KEYS}


def _blend_score_breakdowns(
    deterministic_breakdown: dict[str, float],
    model_breakdown: dict[str, float] | None,
) -> dict[str, float]:
    if not model_breakdown:
        return deterministic_breakdown
    return {
        key: round(
            (deterministic_breakdown[key] * 0.6)
            + (model_breakdown.get(key, deterministic_breakdown[key]) * 0.4),
            2,
        )
        for key in SCORING_KEYS
    }


def _contract_completeness_score(text: str) -> float:
    matched = sum(1 for marker in CONTRACT_MARKERS if marker in text)
    return round(min(0.96, 0.48 + (matched / len(CONTRACT_MARKERS) * 0.5)), 2)


def _assumption_handling_score(text: str, missing_context_count: int) -> float:
    if missing_context_count == 0:
        return 0.92 if "assumptions:" in text else 0.82
    base = 0.9 if "assumptions:" in text else 0.72
    return round(max(0.62, base - min(0.16, missing_context_count * 0.04)), 2)


def _platform_fit_score(text: str, platform: str) -> float:
    target_terms = PLATFORM_TERMS.get(platform, PLATFORM_TERMS["generic"])
    matched = sum(1 for term in target_terms if term in text)
    base = 0.62 + (matched * 0.07)
    if f"target platform: {platform}" in text:
        base += 0.1
    if platform in {"generic", "other"} and "provider-specific" in text:
        base += 0.08
    return round(min(0.96, base), 2)


def _platform_fit_breakdown(text: str) -> dict[str, float]:
    return {
        platform: _platform_fit_score(text, platform)
        for platform in (
            "codex",
            "gemini",
            "claude",
            "chatgpt",
            "cursor",
            "perplexity",
            "copilot",
            "generic",
        )
    }


def _explanation_for_prompt(
    prompt: PromptVariant,
    settings: PromptSettings,
    missing_context_count: int,
    recommendation_notes: list[str],
    session_profile: dict[str, Any],
) -> str:
    display_name = str(session_profile.get("display_name") or "").strip()
    notes = [
        f"{_platform_label(settings.target_platform)} platform",
        f"{settings.format.replace('_', ' ')} format",
        f"{settings.tone.replace('_', ' ')} tone",
        f"{settings.detail_level.replace('_', ' ')} detail",
    ]
    notes.extend(recommendation_notes[:4])
    if missing_context_count:
        notes.append(f"{missing_context_count} explicit assumptions")
    note_text = "; ".join(dict.fromkeys(notes))
    owner = f" for {display_name}" if display_name else ""
    return (
        f"This {prompt.strategy.replace('_', ' ')} draft{owner} turns the request into a "
        f"platform-ready prompt contract shaped by {note_text}."
    )


def _score_metadata_for_prompt(
    problem: str,
    prompt: PromptVariant,
    settings: PromptSettings,
    classification: dict[str, Any],
    assumption_sources: list[dict[str, Any]],
    profile_traits: list[dict[str, Any]],
    session_profile: dict[str, Any],
    scorer_metadata: dict[str, Any],
    recommendation_notes: list[str],
) -> dict[str, Any]:
    text = prompt.prompt_text.lower()
    platform_breakdown = _platform_fit_breakdown(text)
    target_platform = settings.target_platform
    assumption_notes = [
        str(item.get("assumption"))
        for item in assumption_sources
        if item.get("assumption")
    ]
    display_name = str(session_profile.get("display_name") or "").strip()
    platform_label = _platform_label(str(session_profile.get("primary_ai_platform") or target_platform))
    return {
        "platform_fit_rating": platform_breakdown.get(target_platform)
        or platform_breakdown.get("generic"),
        "platform_fit_breakdown": platform_breakdown,
        "recommendation_summary": _recommendation_summary(
            display_name=display_name,
            platform_label=platform_label,
            target_platform=target_platform,
            assumption_count=len(assumption_notes),
        ),
        "why_this_variant": _why_this_variant(prompt, settings, assumption_notes),
        "assumption_notes": assumption_notes,
        "modification_audit_trail": _modification_audit_trail(
            problem=problem,
            settings=settings,
            classification=classification,
            assumption_sources=assumption_sources,
            session_profile=session_profile,
        ),
        "rules_matched": _rules_matched(prompt, settings, classification, assumption_sources),
        "user_trait_alignment": _trait_alignment(profile_traits),
        "optimization_paths": _optimization_paths(
            prompt=prompt,
            settings=settings,
            classification=classification,
            assumption_sources=assumption_sources,
            recommendation_notes=recommendation_notes,
        ),
        "recommended_actions": _recommended_actions(prompt, settings, assumption_notes),
        "scorer_metadata": scorer_metadata,
    }


def _why_this_variant(
    prompt: PromptVariant,
    settings: PromptSettings,
    assumption_notes: list[str],
) -> str:
    platform_reason = PLATFORM_BEHAVIOR_SUMMARIES.get(
        settings.target_platform,
        PLATFORM_BEHAVIOR_SUMMARIES["generic"],
    )
    assumption_text = (
        f" It carries {len(assumption_notes)} explicit assumptions instead of hiding missing context."
        if assumption_notes
        else " It has enough context to avoid major injected assumptions."
    )
    return (
        f"It uses the {prompt.strategy.replace('_', ' ')} strategy and emphasizes "
        f"{platform_reason}.{assumption_text}"
    )


def _recommendation_summary(
    display_name: str,
    platform_label: str,
    target_platform: str,
    assumption_count: int,
) -> str:
    behavior = PLATFORM_BEHAVIOR_SUMMARIES.get(
        target_platform,
        PLATFORM_BEHAVIOR_SUMMARIES["generic"],
    )
    owner = f"{display_name}'s " if display_name else ""
    assumption_note = (
        f" with {assumption_count} visible assumptions"
        if assumption_count
        else " with no major missing-context assumptions"
    )
    return f"{owner}{platform_label}-ready prompt, tuned for {behavior}{assumption_note}."


def _modification_audit_trail(
    problem: str,
    settings: PromptSettings,
    classification: dict[str, Any],
    assumption_sources: list[dict[str, Any]],
    session_profile: dict[str, Any],
) -> list[dict[str, Any]]:
    audit = [
        {
            "id": "raw_request_to_contract",
            "label": "Structured the request",
            "reason": "The raw input was converted into role, task, context, constraints, success criteria, and follow-up behavior.",
            "source": "run_pipeline",
        },
        {
            "id": "domain_context",
            "label": "Added domain context",
            "reason": (
                f"Domain was {classification.get('domain_source', 'detected')} as "
                f"{_labelize(str(classification.get('domain') or 'general'))}."
            ),
            "source": "classifier",
        },
        {
            "id": "platform_fit",
            "label": "Shaped for platform fit",
            "reason": (
                f"The prompt was optimized for {_platform_label(settings.target_platform)}: "
                f"{PLATFORM_BEHAVIOR_SUMMARIES.get(settings.target_platform, PLATFORM_BEHAVIOR_SUMMARIES['generic'])}."
            ),
            "source": "platform_settings",
        },
    ]
    if session_profile.get("display_name"):
        audit.append(
            {
                "id": "session_personalization",
                "label": "Personalized session context",
                "reason": (
                    f"Guidance was attached to {session_profile['display_name']}'s "
                    f"{_labelize(str(session_profile.get('primary_ai_platform') or 'selected'))} session."
                ),
                "source": "session_onboarding",
            }
        )
    if len(problem.split()) < 8:
        audit.append(
            {
                "id": "short_input_expansion",
                "label": "Expanded short input",
                "reason": "The original request was brief, so the prompt adds missing structure and decision criteria.",
                "source": "contract_builder",
            }
        )
    for item in assumption_sources:
        audit.append(
            {
                "id": f"assumption_{item.get('question_id', 'unknown')}",
                "label": "Injected explicit assumption",
                "reason": (
                    f"Question skipped or unanswered: {item.get('question')}. "
                    f"Assumption added: {item.get('assumption')}."
                ),
                "source": "clarifying_questions",
            }
        )
    return audit


def _rules_matched(
    prompt: PromptVariant,
    settings: PromptSettings,
    classification: dict[str, Any],
    assumption_sources: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rules = [
        {
            "id": "phase14_contract_completeness",
            "label": "Prompt contract completeness",
            "matched": True,
            "detail": "Scored role, task, context, constraints, output format, assumptions, and safety boundaries.",
        },
        {
            "id": "phase14_platform_fit",
            "label": "Target platform fit",
            "matched": True,
            "detail": f"Target platform is {_labelize(settings.target_platform)}.",
        },
    ]
    if classification.get("domain_source") in {"user_confirmed", "user_corrected"}:
        rules.append(
            {
                "id": "domain_confirmation",
                "label": "Confirmed domain influence",
                "matched": True,
                "detail": "User-confirmed domain context was carried into scoring.",
            }
        )
    if assumption_sources:
        rules.append(
            {
                "id": "skipped_question_assumptions",
                "label": "Skipped-question assumptions",
                "matched": True,
                "detail": f"{len(assumption_sources)} missing details were surfaced as assumptions.",
            }
        )
    if prompt.strategy == "safety_first":
        rules.append(
            {
                "id": "safety_first_strategy",
                "label": "Safety-first strategy",
                "matched": True,
                "detail": "Risk posture required conservative guidance and escalation boundaries.",
            }
        )
    return rules


def _trait_alignment(profile_traits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "trait_key": trait.get("trait_key"),
            "label": trait.get("trait_label"),
            "score": trait.get("score"),
            "confidence": trait.get("confidence"),
            "used_for": "Adjusted clarification and recommendation emphasis.",
        }
        for trait in profile_traits[:4]
    ]


def _optimization_paths(
    prompt: PromptVariant,
    settings: PromptSettings,
    classification: dict[str, Any],
    assumption_sources: list[dict[str, Any]],
    recommendation_notes: list[str],
) -> list[dict[str, Any]]:
    paths = [
        {
            "id": "input_to_contract",
            "label": "Input to prompt contract",
            "detail": "Converted the request into a reusable AI instruction contract.",
        },
        {
            "id": "platform_shaping",
            "label": f"{_platform_label(settings.target_platform)} shaping",
            "detail": PLATFORM_BEHAVIOR_SUMMARIES.get(
                settings.target_platform,
                PLATFORM_BEHAVIOR_SUMMARIES["generic"],
            ),
        },
        {
            "id": "domain_fit",
            "label": "Domain fit",
            "detail": f"Aligned with {_labelize(str(classification.get('domain') or 'general problem solving'))}.",
        },
    ]
    if assumption_sources:
        paths.append(
            {
                "id": "assumption_visibility",
                "label": "Assumption visibility",
                "detail": "Skipped or unanswered context was made explicit instead of silently guessed.",
            }
        )
    if recommendation_notes:
        paths.append(
            {
                "id": "profile_and_answer_notes",
                "label": "Answer and profile signals",
                "detail": "; ".join(recommendation_notes[:4]),
            }
        )
    if prompt.strategy == "recommended_prompt":
        paths.append(
            {
                "id": "primary_recommendation",
                "label": "Primary recommendation",
                "detail": "Balanced clarity, completeness, platform fit, and user actionability.",
            }
        )
    return paths


def _recommended_actions(
    prompt: PromptVariant,
    settings: PromptSettings,
    assumption_notes: list[str],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    if assumption_notes:
        actions.append(
            {
                "id": "answer_missing_context",
                "label": "Answer Missing Context",
                "impact": "Reduces assumption risk and improves specificity.",
                "priority": "high",
            }
        )
    if settings.source_strictness in {"none", "cite_when_needed"}:
        actions.append(
            {
                "id": "add_source_constraints",
                "label": "Add Source Constraints",
                "impact": "Can improve evidence and platform fit for research-heavy prompts.",
                "priority": "medium",
            }
        )
    if "audience" not in prompt.prompt_text.lower():
        actions.append(
            {
                "id": "add_audience_detail",
                "label": "Add Audience Detail",
                "impact": "Improves tone, depth, examples, and success criteria.",
                "priority": "medium",
            }
        )
    if settings.target_platform in {"codex", "cursor"}:
        actions.append(
            {
                "id": "add_verification_commands",
                "label": "Add Verification Commands",
                "impact": "Improves code-agent handoff and implementation confidence.",
                "priority": "medium",
            }
        )
    return actions[:3]


def _ollama_scorer_result(
    problem: str,
    prompts: list[PromptVariant],
    settings: PromptSettings,
    classification: dict[str, Any],
    assumption_sources: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, dict[str, float]]]:
    runtime = get_settings()
    metadata = _base_scorer_metadata()
    if runtime.llm_provider != "ollama":
        metadata["ollama_status"] = "not_configured"
        return metadata, {}

    model_name = _ollama_model_name(runtime.default_model)
    request_payload = {
        "model": model_name,
        "prompt": _ollama_scorer_prompt(
            problem=problem,
            prompts=prompts,
            settings=settings,
            classification=classification,
            assumption_sources=assumption_sources,
        ),
        "stream": False,
        "format": "json",
        "options": {"temperature": 0, "num_predict": 120},
    }
    request = Request(
        f"{runtime.ollama_base_url.rstrip('/')}/api/generate",
        data=json.dumps(request_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=runtime.ollama_scorer_timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
        parsed = json.loads(str(body.get("response") or "{}"))
        model_scores = _parse_ollama_scores(parsed)
        if not model_scores:
            raise ValueError("Ollama scorer returned no valid scores")
        metadata.update(
            {
                "scorer_version": "phase14-ollama-blended-v1",
                "scorer_source": "ollama_blended",
                "ollama_status": "used",
                "ollama_model": model_name,
                "model_score_count": len(model_scores),
            }
        )
        return metadata, model_scores
    except (HTTPError, OSError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        metadata["ollama_status"] = "unavailable"
        metadata["fallback_reason"] = str(exc)
        return metadata, {}


def _base_scorer_metadata() -> dict[str, Any]:
    settings = get_settings()
    return {
        "scorer_version": "phase14-deterministic-v1",
        "scorer_source": "deterministic_fallback",
        "model_provider": settings.llm_provider,
        "model": settings.default_model,
        "ollama_status": "not_used",
        "pipeline_stage_sources": {
            "classification": "deterministic_classifier",
            "clarifying_questions": "intent_domain_question_generator",
            "template_assembly": "intent_first_template_assembler",
            "scoring": "ollama_when_available_with_deterministic_fallback",
            "run_prompt": "ollama_when_available",
        },
    }


def _ollama_model_name(default_model: str) -> str:
    return default_model.removeprefix("ollama/")


def _ollama_scorer_prompt(
    problem: str,
    prompts: list[PromptVariant],
    settings: PromptSettings,
    classification: dict[str, Any],
    assumption_sources: list[dict[str, Any]],
) -> str:
    variants = [
        {
            "strategy": prompt.strategy,
            "title": prompt.title,
            "signals": _prompt_signal_summary(prompt.prompt_text),
            "excerpt": prompt.prompt_text[:300],
        }
        for prompt in prompts
    ]
    compact_context = {
        "target_platform": settings.target_platform,
        "format": settings.format,
        "risk": settings.risk,
        "domain": classification.get("domain"),
        "risk_level": classification.get("risk_level"),
        "assumption_count": len(assumption_sources),
    }
    return (
        "Return compact JSON only. For each variant strategy, score 0.0 to 1.0 with keys: "
        f"{', '.join(OLLAMA_SCORING_KEYS)}.\n"
        f"Request: {problem[:300]}\n"
        f"Context: {json.dumps(compact_context, default=str)}\n"
        f"Variants: {json.dumps(variants, default=str)}"
    )


def _prompt_signal_summary(prompt_text: str) -> dict[str, Any]:
    text = prompt_text.lower()
    return {
        "chars": len(prompt_text),
        "has_role": "role:" in text,
        "has_task": "task:" in text,
        "has_constraints": "constraints:" in text,
        "has_assumptions": "assumptions:" in text,
        "has_success_criteria": "success criteria:" in text,
        "has_output_format": "output format:" in text,
        "has_platform_behavior": "platform behavior:" in text,
        "has_next_actions": "next actions" in text or "recommended next actions" in text,
        "has_safety": "safety" in text or "source boundaries" in text,
    }


def _parse_ollama_scores(parsed: dict[str, Any]) -> dict[str, dict[str, float]]:
    raw_scores = parsed.get("scores") if isinstance(parsed, dict) else None
    if raw_scores is None and isinstance(parsed, dict):
        variant_scores = parsed.get("variant_strategies") or parsed.get("variants")
        if isinstance(variant_scores, list):
            raw_scores = {
                str(item.get("strategy") or item.get("id") or item.get("title")): (
                    item.get("score") if isinstance(item.get("score"), dict) else item
                )
                for item in variant_scores
                if isinstance(item, dict)
            }
    if raw_scores is None and isinstance(parsed, dict):
        raw_scores = {
            key: value
            for key, value in parsed.items()
            if isinstance(value, dict) and key not in {"metadata", "explanation"}
        }
    if isinstance(raw_scores, list):
        raw_scores = {
            str(item.get("strategy") or item.get("id") or item.get("title")): item
            for item in raw_scores
            if isinstance(item, dict)
        }
    if not isinstance(raw_scores, dict):
        return {}
    model_scores: dict[str, dict[str, float]] = {}
    for key, raw_breakdown in raw_scores.items():
        if not isinstance(raw_breakdown, dict):
            continue
        valid = _validated_model_breakdown(raw_breakdown)
        if valid:
            model_scores[str(key)] = valid
    return model_scores


def _validated_model_breakdown(raw_breakdown: dict[str, Any]) -> dict[str, float]:
    breakdown: dict[str, float] = {}
    for key in SCORING_KEYS:
        raw_value = raw_breakdown.get(key)
        if raw_value is None:
            continue
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        if value > 1 and value <= 100:
            value = value / 100
        breakdown[key] = round(min(1.0, max(0.0, value)), 2)
    return breakdown if len(breakdown) >= 5 else {}


def _classification_dict(
    classification: ClassificationResponse | dict[str, Any] | None,
) -> dict[str, Any]:
    if classification is None:
        return {}
    if isinstance(classification, dict):
        return classification
    return classification.model_dump()


def _labelize(value: str) -> str:
    return value.replace("_", " ").title()


def _platform_label(value: str) -> str:
    labels = {
        "chatgpt": "ChatGPT",
        "codex": "Codex",
        "claude": "Claude",
        "gemini": "Gemini",
        "cursor": "Cursor",
        "grok": "Grok",
        "perplexity": "Perplexity",
        "copilot": "Copilot",
        "generic": "Generic",
        "other": "Other AI",
    }
    return labels.get(value, _labelize(value))
