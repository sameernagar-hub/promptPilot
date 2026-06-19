from app.config import get_settings
from app.models import PromptVariant
from app.schemas import RunPromptResponse


def run_prompt(prompt: PromptVariant) -> RunPromptResponse:
    settings = get_settings()
    preview = prompt.prompt_text[:280].replace("\n", " ")
    return RunPromptResponse(
        prompt_id=prompt.id,
        provider=settings.llm_provider,
        model=settings.default_model,
        output=(
            "Model execution preview. Live completion is not connected in this local build. "
            f"Provider: {settings.llm_provider}. Model: {settings.default_model}. "
            f"Prompt preview: {preview}"
        ),
    )
