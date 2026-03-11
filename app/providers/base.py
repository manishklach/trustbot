from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

from app.domain.enums import EvidenceDirection
from app.domain.models import EvidenceItemRecord


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def make_evidence(
    investigation_id: str,
    artifact_id: str,
    provider: str,
    code: str,
    direction: EvidenceDirection,
    weight: float,
    summary: str,
    details: Dict[str, Any] | None = None,
) -> EvidenceItemRecord:
    return EvidenceItemRecord(
        evidence_id=f"ev_{uuid4().hex[:12]}",
        investigation_id=investigation_id,
        artifact_id=artifact_id,
        provider=provider,
        code=code,
        direction=direction,
        weight=weight,
        summary=summary,
        details=details or {},
        created_at=utc_now(),
    )
