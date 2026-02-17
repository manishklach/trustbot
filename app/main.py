from __future__ import annotations

from fastapi import FastAPI
from app.models import AnalyzeRequest, AnalyzeResponse
from app.router import route_and_analyze
from app.fusion import fuse
from app.evidence import maybe_request_evidence

app = FastAPI(title="WhatsApp Trust Bot (MVP)", version="0.2.0")

@app.post("/v1/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    routed = route_and_analyze(req)
    fused = fuse(routed["signals"], quality_penalty=routed.get("quality_penalty", 0.0))
    evidence = maybe_request_evidence(fused["verdict"], fused["confidence"], req.content_type.value, routed["reason_codes"])

    if evidence is not None:
        next_step = "Need 1 more input to be confident."
    else:
        if fused["verdict"].value == "RISKY":
            next_step = "Do not act on this. Avoid clicking links or sharing OTP. Verify via official channels."
        elif fused["verdict"].value == "SAFE":
            next_step = "Looks safe based on available signals, but stay cautious and verify source if high-stakes."
        else:
            next_step = "Uncertain. Verify source and ask for the original file/link."

    return AnalyzeResponse(
        verdict=fused["verdict"],
        confidence=float(fused["confidence"]),
        reasons=routed["reasons"][:8],
        reason_codes=list(dict.fromkeys(routed["reason_codes"]))[:12],
        next_step=next_step,
        evidence_request=evidence,
        debug={"risk": fused["risk"], **routed["debug"]},
    )

@app.get("/healthz")
def healthz():
    return {"ok": True}
