from __future__ import annotations

import base64
import io
import os
from typing import Dict, Any, List, Tuple, Optional

from app.models import ReasonCode
from app.pipelines.scam_text import analyze_text_scam

def _tesseract_cmd() -> Optional[str]:
    return os.environ.get("TESSERACT_CMD")

def _try_import_ocr():
    try:
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore
        return pytesseract, Image, None
    except Exception as e:
        return None, None, str(e)

def _try_import_pdf():
    try:
        import pdfplumber  # type: ignore
        return pdfplumber, None
    except Exception as e:
        return None, str(e)

def _ocr_image_bytes(img_bytes: bytes) -> str:
    pytesseract, Image, err = _try_import_ocr()
    if pytesseract is None:
        raise RuntimeError(f"OCR deps missing: {err}")

    cmd = _tesseract_cmd()
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd

    img = Image.open(io.BytesIO(img_bytes))
    return pytesseract.image_to_string(img)

def _extract_pdf_text(pdf_bytes: bytes, max_pages: int = 3) -> str:
    pdfplumber, err = _try_import_pdf()
    if pdfplumber is None:
        raise RuntimeError(f"PDF deps missing: {err}")

    text_parts = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for i, page in enumerate(pdf.pages[:max_pages]):
            text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts).strip()

def analyze_document(file_b64: str, mime: Optional[str], name: Optional[str]) -> Dict[str, Any]:
    signals: List[Tuple[str, float]] = []
    reasons: List[str] = []
    reason_codes: List[ReasonCode] = []
    quality_penalty = 0.0

    if not file_b64:
        return {"signals": [("missing_document", 0.5)], "reasons": ["No file provided."], "reason_codes": [ReasonCode.DOC_OCR_UNAVAILABLE], "quality_penalty": 1.0, "debug": {"name": "document_ocr", "error": "missing"}}

    raw = base64.b64decode(file_b64)
    mt = (mime or "").lower()
    nm = (name or "").lower()

    extracted = ""
    method = None
    try:
        if "pdf" in mt or nm.endswith(".pdf"):
            extracted = _extract_pdf_text(raw)
            method = "pdf_text"
        else:
            extracted = _ocr_image_bytes(raw)
            method = "ocr_image"
    except Exception as e:
        reasons.append("Document OCR/text extraction is not available in this environment.")
        reasons.append("Install optional OCR deps (requirements-ocr.txt) and Tesseract, or send the content as text.")
        reason_codes.append(ReasonCode.DOC_OCR_UNAVAILABLE)
        signals.append(("doc_unavailable", 0.5))
        quality_penalty = 0.8
        return {"signals": signals, "reasons": reasons, "reason_codes": reason_codes, "quality_penalty": quality_penalty, "debug": {"name": "document_ocr", "error": str(e), "mime": mt, "name": nm}}

    extracted = (extracted or "").strip()
    if extracted:
        reason_codes.append(ReasonCode.DOC_TEXT_EXTRACTED)
        # run scam heuristics on extracted text
        out = analyze_text_scam(extracted[:4000])
        signals += out["signals"]
        reasons += ["Extracted text analyzed:"] + out["reasons"]
        reason_codes += out["reason_codes"]
    else:
        signals.append(("doc_empty_text", 0.5))
        reasons.append("Could not extract readable text from the document.")
        reason_codes.append(ReasonCode.DOC_OCR_UNAVAILABLE)
        quality_penalty = 0.6

    return {"signals": signals, "reasons": reasons, "reason_codes": reason_codes, "quality_penalty": quality_penalty, "debug": {"name": "document_ocr", "method": method, "mime": mt, "name": nm, "extracted_chars": len(extracted)}}
