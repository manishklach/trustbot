from __future__ import annotations

from typing import Dict, Any, List, Tuple
from urllib.parse import urlparse
import requests

from app.models import ReasonCode

LOGIN_HINTS = ["login", "signin", "sign-in", "verify", "password", "otp", "kyc", "bank", "wallet"]
FORM_HINTS = ["<form", "type=\"password\"", "name=\"password\"", "enter otp", "submit"]

def _safe_get(url: str, timeout: float = 6.0, max_bytes: int = 200_000) -> Dict[str, Any]:
    """Fetch with redirects; cap bytes; return minimal provenance."""
    s = requests.Session()
    try:
        r = s.get(url, allow_redirects=True, timeout=timeout, headers={"User-Agent": "TrustBotMVP/0.2"})
        content = r.content[:max_bytes] if r.content else b""
        chain = [h.url for h in r.history] + [r.url]
        ct = (r.headers.get("Content-Type") or "").lower()
        return {"ok": True, "final_url": r.url, "status": r.status_code, "chain": chain, "content_type": ct, "content": content}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def analyze_provenance(url: str) -> Dict[str, Any]:
    u = (url or "").strip()
    signals: List[Tuple[str, float]] = []
    reasons: List[str] = []
    reason_codes: List[ReasonCode] = []
    debug: Dict[str, Any] = {"name": "provenance", "fetch": None}

    if not u:
        return {"signals": [("missing_url", 0.5)], "reasons": ["No URL provided."], "reason_codes": [], "debug": debug}

    fetch = _safe_get(u)
    debug["fetch"] = {k: v for k, v in fetch.items() if k not in ("content",)}
    if not fetch["ok"]:
        # can't fetch; stay neutral but slightly risky if URL is non-empty
        signals.append(("fetch_failed", 0.5))
        reasons.append("Could not fetch the link for provenance checks (network blocked or site unreachable).")
        return {"signals": signals, "reasons": reasons, "reason_codes": reason_codes, "debug": debug}

    chain = fetch.get("chain", [])
    if len(chain) >= 3:
        signals.append(("redirect_chain", 0.6))
        reasons.append(f"Link redirects multiple times ({len(chain)-1} redirects), which is common in phishing flows.")
        reason_codes.append(ReasonCode.URL_REDIRECT_CHAIN)

    ct = fetch.get("content_type", "")
    if any(x in ct for x in ["application/octet-stream", "application/zip", "application/x-msdownload"]):
        signals.append(("downloadable", 0.7))
        reasons.append("Destination looks like a direct download; be cautious with files from unknown sources.")
        reason_codes.append(ReasonCode.URL_DOWNLOADABLE)

    content = fetch.get("content", b"")
    low = content.lower()
    if any(h.encode("utf-8") in low for h in (s.lower() for s in FORM_HINTS)):
        signals.append(("form_lure", 0.7))
        reasons.append("Page contains form/password-like patterns typical of credential capture pages.")
        reason_codes.append(ReasonCode.URL_FORM_LURE)

    # Keyword-based hints
    final_url = fetch.get("final_url", "")
    if any(k in final_url.lower() for k in LOGIN_HINTS):
        signals.append(("login_keywords", 0.6))
        reasons.append("URL contains login/verification keywords often used in phishing.")
        reason_codes.append(ReasonCode.URL_LOGIN_KEYWORDS)

    if not signals:
        signals.append(("no_strong_provenance_indicators", 0.45))

    return {"signals": signals, "reasons": reasons, "reason_codes": reason_codes, "debug": debug}
