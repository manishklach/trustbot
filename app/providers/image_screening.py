from __future__ import annotations

from typing import List

from app.domain.enums import ArtifactType, EvidenceDirection
from app.domain.models import ArtifactRecord, EvidenceItemRecord
from app.pipelines.image_forensics import analyze_image
from app.providers.base import make_evidence


def collect_image_evidence(artifact: ArtifactRecord) -> List[EvidenceItemRecord]:
    if artifact.type != ArtifactType.IMAGE:
        return []

    out = analyze_image(artifact.payload.get("image_b64") or "")
    evidence: List[EvidenceItemRecord] = []

    for (_, weight), summary, code in zip(out["signals"], out["reasons"], out["reason_codes"]):
        direction = EvidenceDirection.QUALITY if code.value in {"IMG_HEAVY_COMPRESSION", "IMG_LOW_SIGNAL"} else EvidenceDirection.RISK
        evidence.append(
            make_evidence(
                investigation_id=artifact.investigation_id,
                artifact_id=artifact.artifact_id,
                provider="image_screening",
                code=code.value,
                direction=direction,
                weight=weight,
                summary=summary,
                details=out["debug"],
            )
        )
    return evidence
