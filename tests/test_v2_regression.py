from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.schemas.api_requests import V2AnalyzeRequest
from app.services.investigation_service import InvestigationService


def build_service(tmp_path: Path) -> InvestigationService:
    db_path = tmp_path / "trustbot_v2_test.db"
    return InvestigationService.from_db_path(str(db_path))


def disable_network_provenance(monkeypatch) -> None:
    monkeypatch.setattr("app.services.evidence_service.collect_url_fetch_evidence", lambda artifact: [])


def load_cases() -> list[dict]:
    fixture_path = Path(__file__).parent / "fixtures" / "v2_cases.json"
    return json.loads(fixture_path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", load_cases(), ids=lambda case: case["name"])
def test_v2_golden_cases(case: dict, tmp_path: Path, monkeypatch) -> None:
    disable_network_provenance(monkeypatch)
    service = build_service(tmp_path)

    result = service.analyze(V2AnalyzeRequest(artifact=case["artifact"]))
    detail = service.get_investigation(result.investigation_id)

    assert result.verdict.value == case["expected_verdict"]
    assert result.status.value == case["expected_status"]
    assert detail is not None

    if "headline_contains" in case:
        assert case["headline_contains"] in result.headline
    if "reason_contains" in case:
        assert any(case["reason_contains"] in reason.lower() for reason in result.reasons)
    if "next_best_artifact_type" in case:
        assert result.next_best_artifact is not None
        assert result.next_best_artifact.type == case["next_best_artifact_type"]
    if "expected_artifact_types" in case:
        assert [artifact.type.value for artifact in detail.artifacts] == case["expected_artifact_types"]
    if "expected_evidence_codes" in case:
        actual_codes = {item.code for item in detail.evidence_items}
        for code in case["expected_evidence_codes"]:
            assert code in actual_codes
