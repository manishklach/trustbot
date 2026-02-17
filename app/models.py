from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ContentType(str, Enum):
    text = "text"
    link = "link"
    image = "image"
    document = "document"


class Verdict(str, Enum):
    SAFE = "SAFE"
    RISKY = "RISKY"
    UNSURE = "UNSURE"


class ReasonCode(str, Enum):
    # Text / scam
    SCAM_URGENT_LANGUAGE = "SCAM_URGENT_LANGUAGE"
    SCAM_OTP_REQUEST = "SCAM_OTP_REQUEST"
    SCAM_PAYMENT_REVERSAL = "SCAM_PAYMENT_REVERSAL"
    SCAM_KYC_THREAT = "SCAM_KYC_THREAT"
    SCAM_PHONE_CALLBACK = "SCAM_PHONE_CALLBACK"
    # URL / provenance
    URL_SHORTENER = "URL_SHORTENER"
    URL_IP_LITERAL = "URL_IP_LITERAL"
    URL_SUSPICIOUS_TLD = "URL_SUSPICIOUS_TLD"
    URL_NO_TLS = "URL_NO_TLS"
    URL_PUNYCODE = "URL_PUNYCODE"
    URL_REDIRECT_CHAIN = "URL_REDIRECT_CHAIN"
    URL_DOWNLOADABLE = "URL_DOWNLOADABLE"
    URL_FORM_LURE = "URL_FORM_LURE"
    URL_LOGIN_KEYWORDS = "URL_LOGIN_KEYWORDS"
    # Media heuristics
    IMG_HEAVY_COMPRESSION = "IMG_HEAVY_COMPRESSION"
    IMG_TEXTLIKE_EDGES = "IMG_TEXTLIKE_EDGES"
    IMG_LOW_SIGNAL = "IMG_LOW_SIGNAL"
    # Document / OCR
    DOC_OCR_UNAVAILABLE = "DOC_OCR_UNAVAILABLE"
    DOC_TEXT_EXTRACTED = "DOC_TEXT_EXTRACTED"
    # Evidence
    NEED_RESEND_AS_DOCUMENT = "NEED_RESEND_AS_DOCUMENT"
    NEED_SOURCE_URL = "NEED_SOURCE_URL"
    NEED_MORE_CONTEXT = "NEED_MORE_CONTEXT"


class AnalyzeRequest(BaseModel):
    content_type: ContentType
    text: Optional[str] = None
    url: Optional[str] = None

    # base64 (no data URI prefix) for MVP
    image_b64: Optional[str] = None

    # documents: base64 bytes + optional mime
    file_b64: Optional[str] = None
    file_mime: Optional[str] = None
    file_name: Optional[str] = None

    locale: str = "en_IN"
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidenceRequest(BaseModel):
    ask: str
    reason_codes: List[ReasonCode] = Field(default_factory=list)
    expected_artifact: Optional[str] = None


class AnalyzeResponse(BaseModel):
    verdict: Verdict
    confidence: float = Field(ge=0.0, le=1.0)
    reasons: List[str] = Field(default_factory=list)
    reason_codes: List[ReasonCode] = Field(default_factory=list)
    next_step: str
    evidence_request: Optional[EvidenceRequest] = None
    debug: Dict[str, Any] = Field(default_factory=dict)
