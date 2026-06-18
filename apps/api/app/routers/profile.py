from fastapi import APIRouter, HTTPException

from app.schemas import (
    ProfileInsightsResponse,
    ProfileObservationDeleteResponse,
    ProfileObservationUpdateRequest,
    ProfileQuestionRequest,
    ProfileQuestionResponse,
    PromptProfileResponse,
)
from app.services.profile_analyzer import get_prompt_profile, refresh_prompt_profile
from app.services.profile_insights import (
    answer_profile_question,
    correct_profile_observation,
    delete_profile_observation,
    get_profile_insights,
)


router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=PromptProfileResponse)
def read_profile() -> PromptProfileResponse:
    return get_prompt_profile()


@router.post("/refresh", response_model=PromptProfileResponse)
def refresh_profile() -> PromptProfileResponse:
    return refresh_prompt_profile()


@router.get("/insights", response_model=ProfileInsightsResponse)
def read_profile_insights() -> ProfileInsightsResponse:
    return get_profile_insights()


@router.post("/questions", response_model=ProfileQuestionResponse)
def ask_profile_question(payload: ProfileQuestionRequest) -> ProfileQuestionResponse:
    return answer_profile_question(payload)


@router.patch("/observations/{observation_id}", response_model=PromptProfileResponse)
def correct_observation(
    observation_id: str,
    payload: ProfileObservationUpdateRequest,
) -> PromptProfileResponse:
    try:
        profile = correct_profile_observation(observation_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile observation not found")
    return profile


@router.delete("/observations/{observation_id}", response_model=ProfileObservationDeleteResponse)
def delete_observation(observation_id: str) -> ProfileObservationDeleteResponse:
    result = delete_profile_observation(observation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Profile observation not found")
    return result
