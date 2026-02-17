from __future__ import annotations

from typing import Dict, Any, List, Tuple
from app.models import AnalyzeRequest
from app.pipelines.scam_text import analyze_text_scam
from app.pipelines.url_checks import analyze_url
from app.pipelines.provenance import analyze_provenance
from app.pipelines.image_forensics import analyze_image
from app.pipelines.document_ocr import analyze_document

def route_and_analyze(req: AnalyzeRequest) -> Dict[str, Any]:
    signals: List[Tuple[str, float]] = []
    reasons: List[str] = []
    reason_codes = []
    debug: Dict[str, Any] = {"pipelines": []}
    quality_penalty = 0.0

    ct = req.content_type.value

    if ct == "text":
        out = analyze_text_scam(req.text or "")
        signals += out["signals"]; reasons += out["reasons"]; reason_codes += out["reason_codes"]
        debug["pipelines"].append(out["debug"])

        # Extract URL(s) and run URL+provenance checks
        for u in out.get("extracted_urls", []):
            uo = analyze_url(u)
            signals += uo["signals"]; reasons += uo["reasons"]; reason_codes += uo["reason_codes"]
            debug["pipelines"].append(uo["debug"])

            po = analyze_provenance(u)
            signals += po["signals"]; reasons += po["reasons"]; reason_codes += po["reason_codes"]
            debug["pipelines"].append(po["debug"])

    elif ct == "link":
        uo = analyze_url(req.url or "")
        signals += uo["signals"]; reasons += uo["reasons"]; reason_codes += uo["reason_codes"]
        debug["pipelines"].append(uo["debug"])

        po = analyze_provenance(req.url or "")
        signals += po["signals"]; reasons += po["reasons"]; reason_codes += po["reason_codes"]
        debug["pipelines"].append(po["debug"])

    elif ct == "image":
        out = analyze_image(req.image_b64 or "")
        signals += out["signals"]; reasons += out["reasons"]; reason_codes += out["reason_codes"]
        quality_penalty = max(quality_penalty, out.get("quality_penalty", 0.0))
        debug["pipelines"].append(out["debug"])

    elif ct == "document":
        out = analyze_document(req.file_b64 or "", mime=req.file_mime, name=req.file_name)
        signals += out["signals"]; reasons += out["reasons"]; reason_codes += out["reason_codes"]
        quality_penalty = max(quality_penalty, out.get("quality_penalty", 0.0))
        debug["pipelines"].append(out["debug"])

    else:
        reasons.append("Unsupported content type in MVP.")
        debug["pipelines"].append({"name": "unsupported"})

    return {"signals": signals, "reasons": reasons, "reason_codes": reason_codes, "quality_penalty": quality_penalty, "debug": debug}
