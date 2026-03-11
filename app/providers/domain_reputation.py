from __future__ import annotations

from typing import List
from urllib.parse import urlparse

from app.domain.enums import ArtifactType, EvidenceDirection
from app.domain.models import ArtifactRecord, EvidenceItemRecord
from app.providers.base import make_evidence

HIGH_RISK_HINTS = ("verify", "secure", "wallet", "pay", "kyc", "support")
LOW_RISK_DOMAINS = ("gov", "edu")


def collect_domain_reputation_evidence(artifact: ArtifactRecord) -> List[EvidenceItemRecord]:
    if artifact.type != ArtifactType.LINK:
        return []

    url = artifact.payload.get("url") or ""
    host = (urlparse(url).netloc or "").lower()
    if not host:
        return []

    evidence: List[EvidenceItemRecord] = []
    if any(hint in host for hint in HIGH_RISK_HINTS) and host.count(".") >= 2:
        evidence.append(
            make_evidence(
                investigation_id=artifact.investigation_id,
                artifact_id=artifact.artifact_id,
                provider="domain_reputation",
                code="DOMAIN_HIGH_RISK_KEYWORDS",
                direction=EvidenceDirection.RISK,
                weight=0.55,
                summary="The domain uses high-pressure keywords often seen in impersonation and phishing links.",
                details={"host": host},
            )
        )

    tld = host.rsplit(".", 1)[-1] if "." in host else ""
    if tld in LOW_RISK_DOMAINS:
        evidence.append(
            make_evidence(
                investigation_id=artifact.investigation_id,
                artifact_id=artifact.artifact_id,
                provider="domain_reputation",
                code="DOMAIN_LOW_RISK_TLD",
                direction=EvidenceDirection.TRUST,
                weight=0.4,
                summary="The domain uses a lower-risk top-level domain, which is mildly reassuring but not conclusive.",
                details={"host": host},
            )
        )
    return evidence
