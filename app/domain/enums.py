from __future__ import annotations

from enum import Enum


class ArtifactType(str, Enum):
    TEXT = "text"
    LINK = "link"
    IMAGE = "image"
    DOCUMENT = "document"
    CONTEXT = "context"


class InvestigationStatus(str, Enum):
    OPEN = "OPEN"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    ANALYZING = "ANALYZING"
    RESOLVED = "RESOLVED"
    EXPIRED = "EXPIRED"


class V2Verdict(str, Enum):
    RISKY = "RISKY"
    NEED_MORE = "NEED_MORE"
    LIKELY_SAFE = "LIKELY_SAFE"


class EvidenceDirection(str, Enum):
    RISK = "risk"
    TRUST = "trust"
    QUALITY = "quality"
