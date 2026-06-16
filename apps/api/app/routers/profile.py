from fastapi import APIRouter

from app.schemas import PromptProfileResponse
from app.services.profile_analyzer import get_prompt_profile, refresh_prompt_profile


router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=PromptProfileResponse)
def read_profile() -> PromptProfileResponse:
    return get_prompt_profile()


@router.post("/refresh", response_model=PromptProfileResponse)
def refresh_profile() -> PromptProfileResponse:
    return refresh_prompt_profile()
