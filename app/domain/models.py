from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.domain.enums import ArtifactType, EvidenceDirection, InvestigationStatus, V2Verdict


class ArtifactPayload(BaseModel):
    type: ArtifactType
    text: Optional[str] = None
    url: Optional[str] = None
    image_b64: Optional[str] = None
    file_b64: Optional[str] = None
    file_mime: Optional[str] = None
    file_name: Optional[str] = None
    source_label: Optional[str] = None


class InvestigationRecord(BaseModel):
    investigation_id: str
    user_id: Optional[str] = None
    status: InvestigationStatus
    locale: str = "en_IN"
    channel: str = "api"
    current_verdict: V2Verdict = V2Verdict.NEED_MORE
    confidence: float = 0.0
    created_at: datetime
    updated_at: datetime


class ArtifactRecord(BaseModel):
    artifact_id: str
    investigation_id: str
    type: ArtifactType
    mime_type: Optional[str] = None
    file_name: Optional[str] = None
    sha256: str
    source_channel: str = "api"
    text_content: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class EvidenceItemRecord(BaseModel):
    evidence_id: str
    investigation_id: str
    artifact_id: str
    provider: str
    code: str
    direction: EvidenceDirection
    weight: float = Field(ge=0.0, le=1.0)
    summary: str
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class NextBestArtifact(BaseModel):
    type: str
    why: str


class DecisionTrace(BaseModel):
    risk_score: float
    trust_score: float
    quality_penalty: float
    coverage_score: float
    contradiction_score: float


class DecisionResult(BaseModel):
    verdict: V2Verdict
    confidence: float = Field(ge=0.0, le=1.0)
    headline: str
    reasons: List[str] = Field(default_factory=list)
    recommended_action: str
    status: InvestigationStatus
    next_best_artifact: Optional[NextBestArtifact] = None
    trace: DecisionTrace
