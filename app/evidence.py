from __future__ import annotations

from typing import List, Optional
from app.models import EvidenceRequest, ReasonCode, Verdict

def maybe_request_evidence(verdict: Verdict, confidence: float, content_type: str, reason_codes: List[ReasonCode]) -> Optional[EvidenceRequest]:
    if confidence >= 0.6 and verdict != Verdict.UNSURE:
        return None

    if content_type in ("image", "document"):
        return EvidenceRequest(
            ask="I’m not fully confident due to compression/low signal. Please resend the media as a *Document* (not as a photo), or share the original file if available.",
            reason_codes=list(set(reason_codes + [ReasonCode.NEED_RESEND_AS_DOCUMENT])),
            expected_artifact="resend_as_document",
        )

    if content_type in ("text", "link"):
        return EvidenceRequest(
            ask="I’m not fully confident. Can you share the original source link (or where this came from) and 1–2 lines of surrounding context?",
            reason_codes=list(set(reason_codes + [ReasonCode.NEED_SOURCE_URL, ReasonCode.NEED_MORE_CONTEXT])),
            expected_artifact="source_url_or_context",
        )

    return EvidenceRequest(
        ask="I’m not fully confident. Please share a bit more context or the original source.",
        reason_codes=list(set(reason_codes + [ReasonCode.NEED_MORE_CONTEXT])),
        expected_artifact="context",
    )
