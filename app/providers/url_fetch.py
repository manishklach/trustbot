from __future__ import annotations

from typing import List

from app.domain.enums import ArtifactType, EvidenceDirection
from app.domain.models import ArtifactRecord, EvidenceItemRecord
from app.pipelines.provenance import analyze_provenance
from app.providers.base import make_evidence


def collect_url_fetch_evidence(artifact: ArtifactRecord) -> List[EvidenceItemRecord]:
    if artifact.type != ArtifactType.LINK:
        return []

    url = artifact.payload.get("url") or ""
    if not url.strip():
        return []

    out = analyze_provenance(url)
    evidence: List[EvidenceItemRecord] = []
    for (_, weight), summary, code in zip(out["signals"], out["reasons"], out["reason_codes"]):
        evidence.append(
            make_evidence(
                investigation_id=artifact.investigation_id,
                artifact_id=artifact.artifact_id,
                provider="url_fetch",
                code=code.value,
                direction=EvidenceDirection.RISK,
                weight=weight,
                summary=summary,
                details=out["debug"].get("fetch") or {},
            )
        )
    return evidence
