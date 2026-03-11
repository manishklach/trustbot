from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.api_requests import V2AnalyzeRequest, V2ArtifactRequest
from app.schemas.api_responses import InvestigationDetailResponse, V2AnalyzeResponse
from app.services.investigation_service import InvestigationService

router = APIRouter(prefix="/v2/investigations", tags=["investigations"])
service = InvestigationService()


@router.post("/analyze", response_model=V2AnalyzeResponse)
def analyze_investigation(req: V2AnalyzeRequest) -> V2AnalyzeResponse:
    try:
        return service.analyze(req)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{investigation_id}", response_model=InvestigationDetailResponse)
def get_investigation(investigation_id: str) -> InvestigationDetailResponse:
    result = service.get_investigation(investigation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    return result


@router.post("/{investigation_id}/artifacts", response_model=V2AnalyzeResponse)
def add_artifact(investigation_id: str, req: V2ArtifactRequest) -> V2AnalyzeResponse:
    try:
        return service.add_artifact(investigation_id, req)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
