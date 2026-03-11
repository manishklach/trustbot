from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from app.domain.decision import decide_investigation
from app.domain.enums import ArtifactType, InvestigationStatus, V2Verdict
from app.domain.models import ArtifactPayload, ArtifactRecord, InvestigationRecord
from app.pipelines.scam_text import URL_RE
from app.repositories.v2_store import V2Store
from app.schemas.api_requests import V2AnalyzeRequest, V2ArtifactRequest
from app.schemas.api_responses import InvestigationDetailResponse, V2AnalyzeResponse
from app.services.evidence_service import EvidenceService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class InvestigationService:
    def __init__(self, store: Optional[V2Store] = None, evidence_service: Optional[EvidenceService] = None) -> None:
        self.store = store or V2Store(os.environ.get("TRUSTBOT_DB_PATH", "trustbot_v2.db"))
        self.evidence_service = evidence_service or EvidenceService()

    @classmethod
    def from_db_path(cls, db_path: str) -> "InvestigationService":
        return cls(store=V2Store(db_path))

    def analyze(self, req: V2AnalyzeRequest) -> V2AnalyzeResponse:
        investigation = self._load_or_create(req.investigation_id, req.user_id, req.locale, req.channel)
        self._store_artifact_bundle(investigation.investigation_id, req.artifact, req.channel)
        return self._finalize_response(investigation.investigation_id)

    def add_artifact(self, investigation_id: str, req: V2ArtifactRequest) -> V2AnalyzeResponse:
        investigation = self.store.get_investigation(investigation_id)
        if investigation is None:
            raise ValueError("Investigation not found.")
        self._store_artifact_bundle(investigation_id, req.artifact, investigation.channel)
        return self._finalize_response(investigation_id)

    def get_investigation(self, investigation_id: str) -> Optional[InvestigationDetailResponse]:
        investigation = self.store.get_investigation(investigation_id)
        if investigation is None:
            return None
        artifacts = self.store.list_artifacts(investigation_id)
        evidence_items = self.store.list_evidence_items(investigation_id)
        decision = decide_investigation(artifacts, evidence_items)
        return InvestigationDetailResponse(
            investigation_id=investigation.investigation_id,
            status=decision.status,
            verdict=decision.verdict,
            confidence=decision.confidence,
            headline=decision.headline,
            reasons=decision.reasons,
            recommended_action=decision.recommended_action,
            next_best_artifact=decision.next_best_artifact,
            artifacts=artifacts,
            evidence_items=evidence_items,
            trace=decision.trace,
        )

    def _load_or_create(
        self,
        investigation_id: Optional[str],
        user_id: Optional[str],
        locale: str,
        channel: str,
    ) -> InvestigationRecord:
        if investigation_id:
            investigation = self.store.get_investigation(investigation_id)
            if investigation is None:
                raise ValueError("Investigation not found.")
            return investigation

        now = utc_now()
        investigation = InvestigationRecord(
            investigation_id=f"inv_{uuid4().hex[:12]}",
            user_id=user_id,
            status=InvestigationStatus.OPEN,
            locale=locale,
            channel=channel,
            current_verdict=V2Verdict.NEED_MORE,
            confidence=0.0,
            created_at=now,
            updated_at=now,
        )
        self.store.create_investigation(investigation)
        return investigation

    def _build_artifact(self, investigation_id: str, payload: ArtifactPayload, channel: str) -> ArtifactRecord:
        digest_source = (
            payload.text
            or payload.url
            or payload.image_b64
            or payload.file_b64
            or payload.file_name
            or payload.type.value
        )
        text_content = payload.text or payload.url
        return ArtifactRecord(
            artifact_id=f"art_{uuid4().hex[:12]}",
            investigation_id=investigation_id,
            type=payload.type,
            mime_type=payload.file_mime,
            file_name=payload.file_name,
            sha256=hashlib.sha256(digest_source.encode("utf-8")).hexdigest(),
            source_channel=channel,
            text_content=text_content,
            payload=payload.model_dump(),
            created_at=utc_now(),
        )

    def _store_artifact_bundle(self, investigation_id: str, payload: ArtifactPayload, channel: str) -> None:
        artifact = self._build_artifact(investigation_id, payload, channel)
        self.store.add_artifact(artifact)
        self.store.add_evidence_items(self.evidence_service.collect_for_artifact(artifact))

        for derived in self._derive_follow_up_artifacts(investigation_id, payload, channel):
            self.store.add_artifact(derived)
            self.store.add_evidence_items(self.evidence_service.collect_for_artifact(derived))

    def _derive_follow_up_artifacts(
        self,
        investigation_id: str,
        payload: ArtifactPayload,
        channel: str,
    ) -> List[ArtifactRecord]:
        if payload.type not in (ArtifactType.TEXT, ArtifactType.CONTEXT):
            return []

        text = payload.text or ""
        urls = list(dict.fromkeys(URL_RE.findall(text)))
        derived: List[ArtifactRecord] = []
        for url in urls:
            derived_payload = ArtifactPayload(
                type=ArtifactType.LINK,
                url=url,
                source_label="derived_from_text",
            )
            derived.append(self._build_artifact(investigation_id, derived_payload, channel))
        return derived

    def _finalize_response(self, investigation_id: str) -> V2AnalyzeResponse:
        investigation = self.store.get_investigation(investigation_id)
        if investigation is None:
            raise ValueError("Investigation not found.")

        artifacts = self.store.list_artifacts(investigation_id)
        evidence_items = self.store.list_evidence_items(investigation_id)
        decision = decide_investigation(artifacts, evidence_items)

        investigation.status = decision.status
        investigation.current_verdict = decision.verdict
        investigation.confidence = decision.confidence
        investigation.updated_at = utc_now()
        self.store.update_investigation(investigation)

        return V2AnalyzeResponse(
            investigation_id=investigation_id,
            status=decision.status,
            verdict=decision.verdict,
            confidence=decision.confidence,
            headline=decision.headline,
            reasons=decision.reasons,
            recommended_action=decision.recommended_action,
            next_best_artifact=decision.next_best_artifact,
            artifacts_seen=len(artifacts),
            trace=decision.trace,
        )
