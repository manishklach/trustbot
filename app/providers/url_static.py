from __future__ import annotations

from typing import List

from app.domain.enums import ArtifactType, EvidenceDirection
from app.domain.models import ArtifactRecord, EvidenceItemRecord
from app.pipelines.url_checks import analyze_url
from app.providers.base import make_evidence


def collect_url_static_evidence(artifact: ArtifactRecord) -> List[EvidenceItemRecord]:
    if artifact.type != ArtifactType.LINK:
        return []

    url = artifact.payload.get("url") or ""
    if not url.strip():
        return []

    out = analyze_url(url)
    evidence: List[EvidenceItemRecord] = []
    for (_, weight), summary, code in zip(out["signals"], out["reasons"], out["reason_codes"]):
        evidence.append(
            make_evidence(
                investigation_id=artifact.investigation_id,
                artifact_id=artifact.artifact_id,
                provider="url_static",
                code=code.value,
                direction=EvidenceDirection.RISK,
                weight=weight,
                summary=summary,
                details={"url": url},
            )
        )
    return evidence
