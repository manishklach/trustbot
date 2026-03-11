from __future__ import annotations

from collections import Counter
from typing import Iterable, List, Optional

from app.domain.enums import ArtifactType, EvidenceDirection, InvestigationStatus, V2Verdict
from app.domain.models import ArtifactRecord, DecisionResult, DecisionTrace, EvidenceItemRecord, NextBestArtifact


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _weighted_bucket(items: Iterable[EvidenceItemRecord], direction: EvidenceDirection) -> float:
    weights = [item.weight for item in items if item.direction == direction]
    if not weights:
        return 0.0
    return clamp01(sum(weights) / max(1.5, len(weights)))


def _coverage_score(evidence_items: List[EvidenceItemRecord]) -> float:
    providers = {item.provider for item in evidence_items}
    return clamp01(len(providers) / 4.0)


def _contradiction_score(risk_score: float, trust_score: float) -> float:
    if risk_score == 0.0 or trust_score == 0.0:
        return 0.0
    return clamp01(min(risk_score, trust_score))


def _headline_for(verdict: V2Verdict, evidence_items: List[EvidenceItemRecord]) -> str:
    risk_codes = [item.code for item in evidence_items if item.direction == EvidenceDirection.RISK]
    codes = Counter(risk_codes)
    top_code = codes.most_common(1)[0][0] if codes else None

    if verdict == V2Verdict.RISKY and "SCAM_OTP_REQUEST" in risk_codes:
        return "This looks like a likely OTP scam."
    if verdict == V2Verdict.RISKY and "IMPERSONATION_BRAND_DOMAIN_MISMATCH" in risk_codes:
        return "This looks like brand impersonation."
    if verdict == V2Verdict.LIKELY_SAFE:
        return "This looks consistent with a legitimate message."
    return "I need one more artifact to verify this safely."


def _recommended_action(verdict: V2Verdict) -> str:
    if verdict == V2Verdict.RISKY:
        return "Do not click links, share OTPs, send money, or call numbers from the message. Verify through an official channel you open yourself."
    if verdict == V2Verdict.LIKELY_SAFE:
        return "This looks legitimate from the available evidence, but still verify independently if money, identity, or account access is involved."
    return "Please send the one follow-up artifact below so I can verify this more confidently."


def _next_best_artifact(
    verdict: V2Verdict,
    artifacts: List[ArtifactRecord],
    evidence_items: List[EvidenceItemRecord],
) -> Optional[NextBestArtifact]:
    if verdict != V2Verdict.NEED_MORE:
        return None

    artifact_types = {artifact.type for artifact in artifacts}
    evidence_codes = {item.code for item in evidence_items}

    if ArtifactType.IMAGE in artifact_types and "IMG_HEAVY_COMPRESSION" in evidence_codes:
        return NextBestArtifact(
            type="resend_as_document",
            why="The current image is too compressed; sending the original file preserves details for OCR and visual checks.",
        )
    if ArtifactType.TEXT in artifact_types and "TEXT_HAS_URL" in evidence_codes:
        return NextBestArtifact(
            type="source_url",
            why="The original link lets TrustBot inspect redirects, domain reputation, and landing-page behavior.",
        )
    if ArtifactType.TEXT in artifact_types:
        return NextBestArtifact(
            type="context_note",
            why="One or two lines about where the message came from can help separate official notices from forwards and impersonation.",
        )
    return NextBestArtifact(
        type="source_artifact",
        why="A higher-fidelity original file or source link would improve confidence.",
    )


def decide_investigation(artifacts: List[ArtifactRecord], evidence_items: List[EvidenceItemRecord]) -> DecisionResult:
    risk_score = _weighted_bucket(evidence_items, EvidenceDirection.RISK)
    trust_score = _weighted_bucket(evidence_items, EvidenceDirection.TRUST)
    quality_penalty = _weighted_bucket(evidence_items, EvidenceDirection.QUALITY)
    coverage_score = _coverage_score(evidence_items)
    contradiction_score = _contradiction_score(risk_score, trust_score)
    max_risk_weight = max(
        (item.weight for item in evidence_items if item.direction == EvidenceDirection.RISK),
        default=0.0,
    )

    confidence = clamp01(max(risk_score, trust_score) * 0.75 + coverage_score * 0.2 - quality_penalty * 0.3)

    if (
        (risk_score >= 0.85 and coverage_score >= 0.25)
        or (max_risk_weight >= 0.9 and risk_score >= 0.7)
        or (risk_score >= 0.65 and coverage_score >= 0.5 and max_risk_weight >= 0.75)
    ):
        verdict = V2Verdict.RISKY
        status = InvestigationStatus.RESOLVED
    elif trust_score >= 0.85 and contradiction_score < 0.2 and coverage_score >= 0.5:
        verdict = V2Verdict.LIKELY_SAFE
        status = InvestigationStatus.RESOLVED
    else:
        verdict = V2Verdict.NEED_MORE
        status = InvestigationStatus.WAITING_FOR_USER

    unique_reasons: List[str] = []
    for item in sorted(evidence_items, key=lambda current: current.weight, reverse=True):
        if item.summary not in unique_reasons:
            unique_reasons.append(item.summary)
        if len(unique_reasons) == 4:
            break

    if not unique_reasons:
        unique_reasons = ["I do not yet have enough high-quality evidence to verify this confidently."]

    return DecisionResult(
        verdict=verdict,
        confidence=confidence,
        headline=_headline_for(verdict, evidence_items),
        reasons=unique_reasons,
        recommended_action=_recommended_action(verdict),
        status=status,
        next_best_artifact=_next_best_artifact(verdict, artifacts, evidence_items),
        trace=DecisionTrace(
            risk_score=risk_score,
            trust_score=trust_score,
            quality_penalty=quality_penalty,
            coverage_score=coverage_score,
            contradiction_score=contradiction_score,
        ),
    )
