from fastapi import APIRouter

from app.config import get_settings
from app.db import check_database_connection
from app.schemas import HealthResponse


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    database = check_database_connection()
    return HealthResponse(
        service="promptpilot-api",
        status="ok" if database["status"] == "ok" else "degraded",
        database=database,
        model_provider=settings.llm_provider,
        default_model=settings.default_model,
    )
