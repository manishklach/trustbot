from __future__ import annotations

from typing import List

from app.domain.models import ArtifactRecord, EvidenceItemRecord
from app.providers.document_extract import collect_document_evidence
from app.providers.domain_reputation import collect_domain_reputation_evidence
from app.providers.image_screening import collect_image_evidence
from app.providers.impersonation import collect_impersonation_evidence
from app.providers.text_patterns import collect_text_pattern_evidence
from app.providers.url_fetch import collect_url_fetch_evidence
from app.providers.url_static import collect_url_static_evidence


class EvidenceService:
    def collect_for_artifact(self, artifact: ArtifactRecord) -> List[EvidenceItemRecord]:
        evidence: List[EvidenceItemRecord] = []
        for collector in (
            collect_text_pattern_evidence,
            collect_url_static_evidence,
            collect_url_fetch_evidence,
            collect_document_evidence,
            collect_image_evidence,
            collect_impersonation_evidence,
            collect_domain_reputation_evidence,
        ):
            evidence.extend(collector(artifact))
        return evidence
