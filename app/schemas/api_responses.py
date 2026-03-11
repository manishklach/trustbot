from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from app.domain.enums import InvestigationStatus, V2Verdict
from app.domain.models import ArtifactRecord, DecisionTrace, EvidenceItemRecord, NextBestArtifact


class V2AnalyzeResponse(BaseModel):
    investigation_id: str
    status: InvestigationStatus
    verdict: V2Verdict
    confidence: float
    headline: str
    reasons: List[str]
    recommended_action: str
    next_best_artifact: Optional[NextBestArtifact] = None
    artifacts_seen: int
    trace: DecisionTrace


class InvestigationDetailResponse(BaseModel):
    investigation_id: str
    status: InvestigationStatus
    verdict: V2Verdict
    confidence: float
    headline: str
    reasons: List[str]
    recommended_action: str
    next_best_artifact: Optional[NextBestArtifact] = None
    artifacts: List[ArtifactRecord]
    evidence_items: List[EvidenceItemRecord]
    trace: DecisionTrace
