from __future__ import annotations

from typing import List

from app.domain.enums import ArtifactType, EvidenceDirection
from app.domain.models import ArtifactRecord, EvidenceItemRecord
from app.pipelines.scam_text import analyze_text_scam
from app.providers.base import make_evidence


def collect_text_pattern_evidence(artifact: ArtifactRecord) -> List[EvidenceItemRecord]:
    if artifact.type not in (ArtifactType.TEXT, ArtifactType.CONTEXT):
        return []

    text = artifact.payload.get("text") or artifact.text_content or ""
    if not text.strip():
        return []

    out = analyze_text_scam(text)
    evidence: List[EvidenceItemRecord] = []
    for (_, weight), summary, code in zip(out["signals"], out["reasons"], out["reason_codes"]):
        evidence.append(
            make_evidence(
                investigation_id=artifact.investigation_id,
                artifact_id=artifact.artifact_id,
                provider="text_patterns",
                code=code.value,
                direction=EvidenceDirection.RISK,
                weight=weight,
                summary=summary,
            )
        )

    if out.get("extracted_urls"):
        evidence.append(
            make_evidence(
                investigation_id=artifact.investigation_id,
                artifact_id=artifact.artifact_id,
                provider="text_patterns",
                code="TEXT_HAS_URL",
                direction=EvidenceDirection.RISK,
                weight=0.35,
                summary="The message includes a URL that should be checked directly, not trusted from the forward alone.",
                details={"urls": out["extracted_urls"]},
            )
        )
    return evidence
