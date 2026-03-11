from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.domain.models import ArtifactPayload


class V2AnalyzeRequest(BaseModel):
    user_id: Optional[str] = None
    investigation_id: Optional[str] = None
    artifact: ArtifactPayload
    locale: str = "en_IN"
    channel: str = "api"


class V2ArtifactRequest(BaseModel):
    artifact: ArtifactPayload
