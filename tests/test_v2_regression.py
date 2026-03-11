from __future__ import annotations

from pathlib import Path

from app.schemas.api_requests import V2AnalyzeRequest
from app.services.investigation_service import InvestigationService


def build_service(tmp_path: Path) -> InvestigationService:
    db_path = tmp_path / "trustbot_v2_test.db"
    return InvestigationService.from_db_path(str(db_path))


def disable_network_provenance(monkeypatch) -> None:
    monkeypatch.setattr("app.services.evidence_service.collect_url_fetch_evidence", lambda artifact: [])


def test_v2_marks_obvious_otp_text_as_risky(tmp_path: Path, monkeypatch) -> None:
    disable_network_provenance(monkeypatch)
    service = build_service(tmp_path)

    result = service.analyze(
        V2AnalyzeRequest(
            artifact={
                "type": "text",
                "text": "URGENT: Your KYC is pending. Share OTP now to avoid account block.",
            }
        )
    )

    assert result.verdict.value == "RISKY"
    assert result.status.value == "RESOLVED"
    assert "OTP scam" in result.headline


def test_v2_derives_link_artifact_from_text_urls(tmp_path: Path, monkeypatch) -> None:
    disable_network_provenance(monkeypatch)
    service = build_service(tmp_path)

    result = service.analyze(
        V2AnalyzeRequest(
            artifact={
                "type": "text",
                "text": "URGENT: Click https://bit.ly/verify-kyc and share OTP now.",
            }
        )
    )
    detail = service.get_investigation(result.investigation_id)

    assert result.verdict.value == "RISKY"
    assert detail is not None
    assert [artifact.type.value for artifact in detail.artifacts] == ["text", "link"]
    assert any(item.code == "URL_SHORTENER" for item in detail.evidence_items)


def test_v2_requests_more_for_missing_image_signal(tmp_path: Path, monkeypatch) -> None:
    disable_network_provenance(monkeypatch)
    service = build_service(tmp_path)

    result = service.analyze(
        V2AnalyzeRequest(
            artifact={
                "type": "image",
                "image_b64": "",
            }
        )
    )

    assert result.verdict.value == "NEED_MORE"
    assert result.next_best_artifact is not None
    assert result.next_best_artifact.type == "source_artifact"


def test_v2_flags_brand_domain_mismatch_as_risky(tmp_path: Path, monkeypatch) -> None:
    disable_network_provenance(monkeypatch)
    service = build_service(tmp_path)

    result = service.analyze(
        V2AnalyzeRequest(
            artifact={
                "type": "link",
                "url": "https://amazon-secure-login.example.com/signin",
            }
        )
    )

    assert result.verdict.value == "RISKY"
    assert any("official domain" in reason.lower() for reason in result.reasons)
