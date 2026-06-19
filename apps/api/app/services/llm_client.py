import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import get_settings
from app.models import PromptVariant
from app.schemas import RunPromptResponse


def run_prompt(prompt: PromptVariant) -> RunPromptResponse:
    settings = get_settings()
    if settings.llm_provider == "ollama":
        return _run_ollama_prompt(prompt)
    preview = prompt.prompt_text[:280].replace("\n", " ")
    return RunPromptResponse(
        prompt_id=prompt.id,
        provider=settings.llm_provider,
        model=settings.default_model,
        output=(
            "Live prompt execution is only wired for the local Ollama provider in this build. "
            f"Provider: {settings.llm_provider}. Model: {settings.default_model}. "
            f"Prompt preview: {preview}"
        ),
    )


def _run_ollama_prompt(prompt: PromptVariant) -> RunPromptResponse:
    settings = get_settings()
    model_name = settings.default_model.removeprefix("ollama/")
    request_payload = {
        "model": model_name,
        "prompt": prompt.prompt_text,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 900},
    }
    request = Request(
        f"{settings.ollama_base_url.rstrip('/')}/api/generate",
        data=json.dumps(request_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=settings.ollama_scorer_timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
        output = str(body.get("response") or "").strip()
        if not output:
            raise ValueError("Ollama returned an empty response")
        return RunPromptResponse(
            prompt_id=prompt.id,
            provider=settings.llm_provider,
            model=model_name,
            output=output,
        )
    except (HTTPError, OSError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        preview = prompt.prompt_text[:280].replace("\n", " ")
        return RunPromptResponse(
            prompt_id=prompt.id,
            provider=settings.llm_provider,
            model=model_name,
            output=(
                "Live Ollama run unavailable; returning a prompt preview instead. "
                f"Reason: {exc}. Prompt preview: {preview}"
            ),
        )
