from fastapi import APIRouter, HTTPException

from app.schemas import (
    PromptIntelligenceAnalyzeRequest,
    PromptIntelligenceReportResponse,
)
from app.services.prompt_intelligence import (
    analyze_prompt_intelligence,
    get_latest_prompt_intelligence_report,
    get_prompt_intelligence_report,
    list_prompt_intelligence_reports,
)


router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.post("/analyze", response_model=PromptIntelligenceReportResponse, status_code=201)
def analyze_prompts(
    payload: PromptIntelligenceAnalyzeRequest,
) -> PromptIntelligenceReportResponse:
    try:
        return analyze_prompt_intelligence(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/reports", response_model=list[PromptIntelligenceReportResponse])
def list_reports() -> list[PromptIntelligenceReportResponse]:
    return list_prompt_intelligence_reports()


@router.get("/reports/latest", response_model=PromptIntelligenceReportResponse | None)
def latest_report() -> PromptIntelligenceReportResponse | None:
    return get_latest_prompt_intelligence_report()


@router.get("/reports/{report_id}", response_model=PromptIntelligenceReportResponse)
def read_report(report_id: str) -> PromptIntelligenceReportResponse:
    report = get_prompt_intelligence_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Prompt intelligence report not found")
    return report
