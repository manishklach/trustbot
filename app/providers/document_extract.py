from __future__ import annotations

from typing import List

from app.domain.enums import ArtifactType, EvidenceDirection
from app.domain.models import ArtifactRecord, EvidenceItemRecord
from app.pipelines.document_ocr import analyze_document
from app.providers.base import make_evidence


def collect_document_evidence(artifact: ArtifactRecord) -> List[EvidenceItemRecord]:
    if artifact.type != ArtifactType.DOCUMENT:
        return []

    out = analyze_document(
        artifact.payload.get("file_b64") or "",
        mime=artifact.mime_type,
        name=artifact.file_name,
    )
    evidence: List[EvidenceItemRecord] = []

    for (_, weight), summary, code in zip(out["signals"], out["reasons"], out["reason_codes"]):
        direction = EvidenceDirection.QUALITY if "DOC_" in code.value else EvidenceDirection.RISK
        evidence.append(
            make_evidence(
                investigation_id=artifact.investigation_id,
                artifact_id=artifact.artifact_id,
                provider="document_extract",
                code=code.value,
                direction=direction,
                weight=weight,
                summary=summary,
                details=out["debug"],
            )
        )
    return evidence
