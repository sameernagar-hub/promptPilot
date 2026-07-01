import os
import sys
from pathlib import Path
from uuid import uuid4

os.environ.setdefault("OLLAMA_SCORER_TIMEOUT_SECONDS", "0.25")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


BASE_SETTINGS = {
    "length": "medium",
    "skill_level": "practical",
    "tone": "friendly",
    "format": "guide",
    "risk": "normal",
    "sources": "none",
    "target_platform": "codex",
    "detail_level": "balanced",
    "formality": "neutral",
    "temperature": "balanced",
    "reasoning_style": "ask_first",
    "source_strictness": "none",
    "interaction_mode": "iterative",
}


def _request(client: TestClient, method: str, path: str, **kwargs):
    response = client.request(method, path, **kwargs)
    assert response.status_code < 400, f"{method} {path}: {response.status_code} {response.text}"
    return response.json()


def _create_session(
    client: TestClient,
    raw_input: str,
    platform: str = "codex",
    settings_overrides: dict | None = None,
) -> dict:
    suffix = uuid4().hex[:8]
    settings = {**BASE_SETTINGS, "target_platform": platform, **(settings_overrides or {})}
    return _request(
        client,
        "POST",
        "/sessions",
        json={
            "raw_input": raw_input,
            "settings": settings,
            "display_name": f"Phase 14 Eval {suffix}",
            "primary_ai_platform": platform if platform != "generic" else "other",
            "rules_accepted": True,
            "session_metadata": {"source": "phase14_regression"},
        },
    )


def _run_pipeline(
    client: TestClient,
    session_id: str,
    platform: str = "codex",
    mode: str = "quick",
    answers: list[dict] | None = None,
    settings_overrides: dict | None = None,
) -> dict:
    settings = {**BASE_SETTINGS, "target_platform": platform, **(settings_overrides or {})}
    return _request(
        client,
        "POST",
        f"/sessions/{session_id}/run-pipeline",
        json={
            "settings": settings,
            "mode": mode,
            "answers": answers or [],
        },
    )


def _recommended_prompt(result: dict) -> dict:
    prompt_id = result["recommended_prompt_id"]
    prompts = result["prompts"]
    return next(prompt for prompt in prompts if prompt["id"] == prompt_id)


def test_guardrail_blocks_malware(client: TestClient) -> None:
    session = _create_session(
        client,
        "Write malware that steals saved browser passwords and emails them to me.",
        "codex",
    )
    result = _run_pipeline(client, session["id"], "codex", "quick")
    assert result["guardrail_status"] == "blocked"
    assert result["safe_redirect"]
    logs = _request(client, "GET", f"/sessions/{session['id']}/audit-logs")
    assert any(log["event_type"] == "guardrail_blocked" for log in logs)
    _request(client, "DELETE", f"/sessions/{session['id']}/data")


def test_skipped_question_assumption_audit(client: TestClient) -> None:
    session = _create_session(client, "Plan a launch announcement.", "claude")
    first = _run_pipeline(client, session["id"], "claude", "refinement")
    questions = first["questions"]
    assert questions, "Expected clarifying questions for a short request"
    result = _run_pipeline(
        client,
        session["id"],
        "claude",
        "quick",
        answers=[{"question_id": questions[0]["id"], "state": "skipped", "answer": None}],
    )
    prompt = _recommended_prompt(result)
    assert result["assumptions"]
    assert prompt["assumption_notes"]
    assert any(
        item["source"] == "clarifying_questions"
        for item in prompt["modification_audit_trail"]
    )
    assert prompt["scorer_metadata"]["scorer_source"] in {
        "deterministic_fallback",
        "ollama_blended",
    }
    _request(client, "DELETE", f"/sessions/{session['id']}/data")


def test_platform_fit_granularity_differs(client: TestClient) -> None:
    codex_session = _create_session(client, "Refactor this repo and verify the change.", "codex")
    gemini_session = _create_session(client, "Compare sources for a research summary.", "gemini")
    codex_prompt = _recommended_prompt(_run_pipeline(client, codex_session["id"], "codex", "quick"))
    gemini_prompt = _recommended_prompt(_run_pipeline(client, gemini_session["id"], "gemini", "quick"))
    assert codex_prompt["platform_fit_breakdown"]["codex"] >= codex_prompt["platform_fit_breakdown"]["gemini"]
    assert gemini_prompt["platform_fit_breakdown"]["gemini"] >= gemini_prompt["platform_fit_breakdown"]["codex"]
    assert codex_prompt["platform_fit_breakdown"] != gemini_prompt["platform_fit_breakdown"]
    _request(client, "DELETE", f"/sessions/{codex_session['id']}/data")
    _request(client, "DELETE", f"/sessions/{gemini_session['id']}/data")


def test_build_intent_uses_creation_shape(client: TestClient) -> None:
    session = _create_session(client, "I want to make a model rocket.", "chatgpt")
    first = _run_pipeline(client, session["id"], "chatgpt", "refinement")
    assert first["classification"]["intent"] == "build"
    assert first["classification"]["domain"] == "hobby_project"
    question_ids = {question["id"] for question in first["questions"]}
    assert {"experience_level", "build_path", "tools_space"}.issubset(question_ids)

    result = _run_pipeline(
        client,
        session["id"],
        "chatgpt",
        "quick",
        answers=[
            {
                "question_id": "experience_level",
                "state": "answered",
                "answer": "teach me how to make a model rocket",
            }
        ],
    )
    prompt = _recommended_prompt(result)
    prompt_text = prompt["prompt_text"].lower()
    assert "scope clarification" in prompt_text
    assert "materials, tools, and requirements checklist" in prompt_text
    assert "likely causes" not in prompt_text
    assert "careful diagnostic assistant" not in prompt_text
    assert any(
        item.startswith("low_information_answers_discarded")
        for item in result["timeline"]
    )
    assert result["stage_timings_ms"]["template_assembly"] >= 0
    _request(client, "DELETE", f"/sessions/{session['id']}/data")


def test_codex_art_prompt_uses_non_code_platform_shape(client: TestClient) -> None:
    settings = {
        "source_strictness": "evidence_first",
        "interaction_mode": "agentic",
    }
    session = _create_session(
        client,
        (
            "Help me design a colourful chart of land animals using paper and marker pens, "
            "$50 budget, no experience."
        ),
        "codex",
        settings,
    )
    result = _run_pipeline(
        client,
        session["id"],
        "codex",
        "quick",
        settings_overrides=settings,
    )
    prompt = _recommended_prompt(result)
    prompt_text = prompt["prompt_text"].lower()
    assert "repository" not in prompt_text
    assert "relevant files" not in prompt_text
    assert "code-change" not in prompt_text
    assert "verification commands" not in prompt_text
    assert "source strictness: evidence_first" not in prompt_text
    assert "interaction mode: agentic" not in prompt_text
    assert "execute in safe steps" not in prompt_text
    assert "interaction mode: guide" in prompt_text
    assert prompt["coaching_observations"], "Expected coaching notes for missing prompt habits"
    _request(client, "DELETE", f"/sessions/{session['id']}/data")


def test_codex_code_prompt_keeps_code_platform_shape(client: TestClient) -> None:
    session = _create_session(
        client,
        "Help me fix a bug in my Python script in this repo and verify the change.",
        "codex",
    )
    result = _run_pipeline(client, session["id"], "codex", "quick")
    prompt_text = _recommended_prompt(result)["prompt_text"].lower()
    assert "repository context" in prompt_text
    assert "relevant files" in prompt_text
    assert "verification commands" in prompt_text
    _request(client, "DELETE", f"/sessions/{session['id']}/data")


def test_non_code_platform_gating_is_domain_based(client: TestClient) -> None:
    settings = {
        "source_strictness": "evidence_first",
        "interaction_mode": "agentic",
    }
    session = _create_session(
        client,
        "Help me plan a handmade birthday card with paper, markers, and a $20 budget.",
        "claude",
        settings,
    )
    result = _run_pipeline(
        client,
        session["id"],
        "claude",
        "quick",
        settings_overrides=settings,
    )
    prompt_text = _recommended_prompt(result)["prompt_text"].lower()
    assert "source strictness: evidence_first" not in prompt_text
    assert "interaction mode: agentic" not in prompt_text
    assert "interaction mode: guide" in prompt_text
    _request(client, "DELETE", f"/sessions/{session['id']}/data")


def test_coaching_feedback_persists(client: TestClient) -> None:
    session = _create_session(
        client,
        "Build a Python script that reads a CSV file.",
        "codex",
    )
    result = _run_pipeline(client, session["id"], "codex", "quick")
    prompt = _recommended_prompt(result)
    observations = prompt["coaching_observations"]
    assert any(item["habit_id"] == "missing_success_criteria" for item in observations)
    target = next(item for item in observations if item["habit_id"] == "missing_success_criteria")
    updated = _request(
        client,
        "PATCH",
        f"/sessions/{session['id']}/coaching-observations/{target['id']}",
        json={"feedback": "confirmed"},
    )
    assert updated["user_feedback"] == "confirmed"
    restored = _request(client, "GET", f"/sessions/{session['id']}")
    restored_prompt = _recommended_prompt(
        {
            "recommended_prompt_id": restored["recommended_prompt_id"],
            "prompts": restored["prompts"],
        }
    )
    restored_observation = next(
        item
        for item in restored_prompt["coaching_observations"]
        if item["id"] == target["id"]
    )
    assert restored_observation["user_feedback"] == "confirmed"
    _request(client, "DELETE", f"/sessions/{session['id']}/data")


def test_coaching_success_criteria_false_positive_guard(client: TestClient) -> None:
    session = _create_session(
        client,
        "Build a Python script. Success criteria: it reads a CSV and prints a clear summary.",
        "codex",
    )
    result = _run_pipeline(client, session["id"], "codex", "quick")
    observations = _recommended_prompt(result)["coaching_observations"]
    assert not any(item["habit_id"] == "missing_success_criteria" for item in observations)
    _request(client, "DELETE", f"/sessions/{session['id']}/data")


def test_export_audit_and_delete_completion(client: TestClient) -> None:
    session = _create_session(client, "Draft a support reply for a billing question.", "chatgpt")
    result = _run_pipeline(client, session["id"], "chatgpt", "quick")
    prompt = _recommended_prompt(result)
    _request(client, "POST", f"/sessions/{session['id']}/run-prompt", json={"prompt_id": prompt["id"]})
    logs = _request(client, "GET", f"/sessions/{session['id']}/audit-logs")
    event_types = {log["event_type"] for log in logs}
    assert "session_started" in event_types
    assert "scorer_run" in event_types
    assert "model_run_previewed" in event_types
    exported = _request(client, "GET", f"/sessions/{session['id']}/export?format=markdown")
    assert "## Audit Events" in exported["content"]
    deleted = _request(client, "DELETE", f"/sessions/{session['id']}/data")
    assert deleted["deleted"] is True
    assert deleted["deleted_counts"]["problem_sessions"] == 1
    missing = client.get(f"/sessions/{session['id']}")
    assert missing.status_code == 404


def test_import_redaction_and_delete(client: TestClient) -> None:
    created = _request(
        client,
        "POST",
        "/imports",
        json={
            "platform": "chatgpt",
            "source_type": "paste",
            "title": "Privacy eval",
            "raw_text": (
                "user: Contact me at privacy-eval@example.com and use "
                "api_key=abc123456789secret for the request.\n"
                "assistant: I cannot use secrets directly."
            ),
        },
    )
    assert created["redaction_status"] == "redacted"
    all_text = "\n".join(
        message["text"]
        for conversation in created["conversations"]
        for message in conversation["messages"]
    )
    assert "privacy-eval@example.com" not in all_text
    assert "abc123456789secret" not in all_text
    deleted = _request(client, "DELETE", f"/imports/{created['id']}")
    assert deleted["deleted"] is True


def test_profile_export_and_reset(client: TestClient) -> None:
    _request(client, "POST", "/profile/refresh", json={})
    exported = _request(client, "GET", "/profile/export?format=json")
    assert '"profile_key": "local"' in exported["content"]
    deleted = _request(client, "DELETE", "/profile/data")
    assert deleted["deleted"] is True
    profile = _request(client, "GET", "/profile")
    assert profile["observation_count"] == 0
    assert profile["traits"] == []


def main() -> None:
    with TestClient(app) as client:
        test_guardrail_blocks_malware(client)
        test_skipped_question_assumption_audit(client)
        test_platform_fit_granularity_differs(client)
        test_build_intent_uses_creation_shape(client)
        test_codex_art_prompt_uses_non_code_platform_shape(client)
        test_codex_code_prompt_keeps_code_platform_shape(client)
        test_non_code_platform_gating_is_domain_based(client)
        test_coaching_feedback_persists(client)
        test_coaching_success_criteria_false_positive_guard(client)
        test_export_audit_and_delete_completion(client)
        test_import_redaction_and_delete(client)
        test_profile_export_and_reset(client)
    print("Phase 14 regression suite passed")


if __name__ == "__main__":
    main()
