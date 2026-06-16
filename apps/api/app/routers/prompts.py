from fastapi import APIRouter, HTTPException

from app.db import store
from app.models import SavedPrompt
from app.schemas import SavePromptRequest, SavedPromptResponse


router = APIRouter(tags=["prompts"])


@router.post("/prompts/{prompt_id}/save", response_model=SavedPromptResponse, status_code=201)
def save_prompt(
    prompt_id: str,
    payload: SavePromptRequest | None = None,
) -> SavedPromptResponse:
    prompt = store.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    saved_prompt = SavedPrompt(
        prompt_id=prompt.id,
        session_id=prompt.session_id,
        title=prompt.title,
        prompt_text=prompt.prompt_text,
        strategy=prompt.strategy,
        label=payload.label if payload else None,
    )
    store.save_prompt(saved_prompt)
    return SavedPromptResponse.model_validate(saved_prompt)


@router.get("/saved-prompts", response_model=list[SavedPromptResponse])
def list_saved_prompts() -> list[SavedPromptResponse]:
    return [
        SavedPromptResponse.model_validate(saved_prompt)
        for saved_prompt in store.list_saved_prompts()
    ]
