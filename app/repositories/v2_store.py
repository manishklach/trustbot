from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional

from app.domain.models import ArtifactRecord, EvidenceItemRecord, InvestigationRecord


class V2Store:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS investigations (
                    investigation_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    investigation_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evidence_items (
                    evidence_id TEXT PRIMARY KEY,
                    investigation_id TEXT NOT NULL,
                    artifact_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )

    def create_investigation(self, investigation: InvestigationRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO investigations (investigation_id, payload_json) VALUES (?, ?)",
                (investigation.investigation_id, investigation.model_dump_json()),
            )

    def update_investigation(self, investigation: InvestigationRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE investigations SET payload_json = ? WHERE investigation_id = ?",
                (investigation.model_dump_json(), investigation.investigation_id),
            )

    def get_investigation(self, investigation_id: str) -> Optional[InvestigationRecord]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM investigations WHERE investigation_id = ?",
                (investigation_id,),
            ).fetchone()
        if row is None:
            return None
        return InvestigationRecord.model_validate_json(row["payload_json"])

    def add_artifact(self, artifact: ArtifactRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO artifacts (artifact_id, investigation_id, payload_json) VALUES (?, ?, ?)",
                (artifact.artifact_id, artifact.investigation_id, artifact.model_dump_json()),
            )

    def list_artifacts(self, investigation_id: str) -> List[ArtifactRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload_json FROM artifacts WHERE investigation_id = ? ORDER BY rowid ASC",
                (investigation_id,),
            ).fetchall()
        return [ArtifactRecord.model_validate_json(row["payload_json"]) for row in rows]

    def add_evidence_items(self, items: List[EvidenceItemRecord]) -> None:
        if not items:
            return
        with self._connect() as conn:
            conn.executemany(
                "INSERT INTO evidence_items (evidence_id, investigation_id, artifact_id, payload_json) VALUES (?, ?, ?, ?)",
                [
                    (item.evidence_id, item.investigation_id, item.artifact_id, item.model_dump_json())
                    for item in items
                ],
            )

    def list_evidence_items(self, investigation_id: str) -> List[EvidenceItemRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload_json FROM evidence_items WHERE investigation_id = ? ORDER BY rowid ASC",
                (investigation_id,),
            ).fetchall()
        return [EvidenceItemRecord.model_validate_json(row["payload_json"]) for row in rows]
