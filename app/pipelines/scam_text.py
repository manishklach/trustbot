from __future__ import annotations

import re
from typing import Dict, Any, List, Tuple
from app.models import ReasonCode

URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)

def analyze_text_scam(text: str) -> Dict[str, Any]:
    t = (text or "").strip()
    tl = t.lower()

    signals: List[Tuple[str, float]] = []
    reasons: List[str] = []
    reason_codes: List[ReasonCode] = []

    urgent_words = ["urgent", "immediately", "act now", "last chance", "final warning", "blocked", "suspended", "freeze"]
    if any(w in tl for w in urgent_words):
        signals.append(("urgent_language", 0.65))
        reasons.append("Uses urgent/threatening language designed to rush you.")
        reason_codes.append(ReasonCode.SCAM_URGENT_LANGUAGE)

    if "otp" in tl or "one time password" in tl:
        signals.append(("otp_request", 0.9))
        reasons.append("Asks for an OTP — a common scam pattern.")
        reason_codes.append(ReasonCode.SCAM_OTP_REQUEST)

    if "kyc" in tl and ("block" in tl or "suspend" in tl or "freeze" in tl):
        signals.append(("kyc_threat", 0.8))
        reasons.append("Threatens account action tied to KYC — common social-engineering tactic.")
        reason_codes.append(ReasonCode.SCAM_KYC_THREAT)

    if "upi" in tl and ("reversal" in tl or "chargeback" in tl or "refund" in tl or "collect" in tl):
        signals.append(("upi_reversal", 0.75))
        reasons.append("Mentions UPI reversal/refund/collect — often used to trick users into approving a collect request.")
        reason_codes.append(ReasonCode.SCAM_PAYMENT_REVERSAL)

    if re.search(r"\bcall\b|\bphone\b|\bhelpline\b", tl) and re.search(r"\+?\d[\d\-\s]{7,}", tl):
        signals.append(("phone_callback", 0.7))
        reasons.append("Asks you to call a number — often used to move the scam off-platform.")
        reason_codes.append(ReasonCode.SCAM_PHONE_CALLBACK)

    extracted_urls = URL_RE.findall(t)
    debug = {"name": "scam_text", "len": len(t), "urls": extracted_urls}

    if not signals and t:
        signals.append(("no_strong_text_indicators", 0.45))

    return {"signals": signals, "reasons": reasons, "reason_codes": reason_codes, "extracted_urls": extracted_urls, "debug": debug}
