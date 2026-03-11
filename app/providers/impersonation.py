from __future__ import annotations

from typing import List, Optional
from urllib.parse import urlparse

from app.domain.enums import ArtifactType, EvidenceDirection
from app.domain.models import ArtifactRecord, EvidenceItemRecord
from app.providers.base import make_evidence

BRANDS = {
    "hdfc": "hdfcbank.com",
    "sbi": "sbi.co.in",
    "icici": "icicibank.com",
    "amazon": "amazon.in",
    "whatsapp": "whatsapp.com",
    "irs": "irs.gov",
    "fedex": "fedex.com",
}


def _claimed_brand(text: str) -> Optional[str]:
    lowered = text.lower()
    for keyword in BRANDS:
        if keyword in lowered:
            return keyword
    return None


def collect_impersonation_evidence(artifact: ArtifactRecord) -> List[EvidenceItemRecord]:
    evidence: List[EvidenceItemRecord] = []

    if artifact.type == ArtifactType.TEXT:
        text = artifact.payload.get("text") or artifact.text_content or ""
        brand = _claimed_brand(text)
        if brand:
            evidence.append(
                make_evidence(
                    investigation_id=artifact.investigation_id,
                    artifact_id=artifact.artifact_id,
                    provider="impersonation",
                    code="CLAIMED_ENTITY_PRESENT",
                    direction=EvidenceDirection.RISK,
                    weight=0.25,
                    summary=f"The message claims to involve {brand.upper()}, so the source domain and sender should match carefully.",
                    details={"claimed_brand": brand},
                )
            )

    if artifact.type == ArtifactType.LINK:
        url = artifact.payload.get("url") or ""
        host = (urlparse(url).netloc or "").lower()
        for brand, official_domain in BRANDS.items():
            if brand in host and official_domain not in host:
                evidence.append(
                    make_evidence(
                        investigation_id=artifact.investigation_id,
                        artifact_id=artifact.artifact_id,
                        provider="impersonation",
                        code="IMPERSONATION_BRAND_DOMAIN_MISMATCH",
                        direction=EvidenceDirection.RISK,
                        weight=0.9,
                        summary=f"The link mentions {brand.upper()} but does not use its expected official domain.",
                        details={"host": host, "expected_domain": official_domain},
                    )
                )
        if host in BRANDS.values():
            evidence.append(
                make_evidence(
                    investigation_id=artifact.investigation_id,
                    artifact_id=artifact.artifact_id,
                    provider="impersonation",
                    code="OFFICIAL_DOMAIN_MATCH",
                    direction=EvidenceDirection.TRUST,
                    weight=0.8,
                    summary="The link host matches a known official domain pattern.",
                    details={"host": host},
                )
            )
    return evidence
