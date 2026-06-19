import json
from typing import Literal

from fastapi import APIRouter, HTTPException

from app.schemas import (
    DeleteProfileDataResponse,
    ProfileExportResponse,
    ProfileInsightsResponse,
    ProfileObservationDeleteResponse,
    ProfileObservationUpdateRequest,
    ProfileQuestionRequest,
    ProfileQuestionResponse,
    PromptProfileResponse,
)
from app.services.profile_analyzer import (
    get_prompt_profile,
    refresh_prompt_profile,
    reset_prompt_profile_data,
)
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


@router.get("/export", response_model=ProfileExportResponse)
def export_profile(
    format: Literal["markdown", "json"] = "markdown",
) -> ProfileExportResponse:
    profile = get_prompt_profile()
    payload = profile.model_dump(mode="json")
    if format == "json":
        content = json.dumps(payload, indent=2)
        filename = "promptpilot-profile.json"
    else:
        content = _profile_export_markdown(payload)
        filename = "promptpilot-profile.md"
    return ProfileExportResponse(
        format=format,
        filename=filename,
        content=content,
        metadata={
            "trait_count": len(profile.traits),
            "platform_preference_count": len(profile.platform_preferences),
            "status": profile.status,
        },
    )


@router.delete("/data", response_model=DeleteProfileDataResponse)
def delete_profile_data() -> DeleteProfileDataResponse:
    counts = reset_prompt_profile_data()
    return DeleteProfileDataResponse(deleted=True, deleted_counts=counts)


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


def _profile_export_markdown(payload: dict) -> str:
    lines = [
        "# PromptPilot Profile",
        "",
        f"- Status: {payload.get('status')}",
        f"- Sessions summarized: {payload.get('total_sessions')}",
        f"- Imports summarized: {payload.get('total_imports')}",
        f"- Observations: {payload.get('observation_count')}",
        "",
        "## Summary",
        "",
        str((payload.get("summary") or {}).get("headline") or "No profile summary yet."),
        "",
        "## Traits",
        "",
    ]
    traits = payload.get("traits") or []
    if traits:
        for trait in traits:
            lines.append(
                f"- {trait.get('trait_label')}: {trait.get('summary')} "
                f"({round(float(trait.get('confidence') or 0) * 100)}% confidence)"
            )
    else:
        lines.append("No profile traits are currently stored.")
    lines.extend(["", "## Platform Preferences", ""])
    preferences = payload.get("platform_preferences") or []
    if preferences:
        for preference in preferences:
            lines.append(
                f"- {preference.get('platform')}: "
                f"{round(float(preference.get('confidence') or 0) * 100)}% confidence"
            )
    else:
        lines.append("No platform preferences are currently stored.")
    lines.append("")
    return "\n".join(lines)
