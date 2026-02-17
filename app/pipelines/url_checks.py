from __future__ import annotations

import re
from urllib.parse import urlparse
from typing import Dict, Any, List, Tuple
from app.models import ReasonCode

SHORTENERS = {"bit.ly", "t.co", "tinyurl.com", "goo.gl", "is.gd", "cutt.ly"}
SUSPICIOUS_TLDS = {"zip", "mov", "top", "xyz", "click", "cam", "quest"}
IP_RE = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")

def analyze_url(url: str) -> Dict[str, Any]:
    u = (url or "").strip()
    signals: List[Tuple[str, float]] = []
    reasons: List[str] = []
    reason_codes: List[ReasonCode] = []

    try:
        p = urlparse(u)
        host = (p.netloc or "").split(":")[0].lower()
        scheme = (p.scheme or "").lower()
    except Exception:
        host = ""
        scheme = ""

    if host in SHORTENERS:
        signals.append(("url_shortener", 0.75))
        reasons.append("Link uses a URL shortener, which often hides the true destination.")
        reason_codes.append(ReasonCode.URL_SHORTENER)

    if host and IP_RE.match(host):
        signals.append(("ip_literal", 0.8))
        reasons.append("Link uses a raw IP address — uncommon for legitimate services.")
        reason_codes.append(ReasonCode.URL_IP_LITERAL)

    if scheme and scheme != "https":
        signals.append(("no_tls", 0.6))
        reasons.append("Link is not HTTPS.")
        reason_codes.append(ReasonCode.URL_NO_TLS)

    if "xn--" in host:
        signals.append(("punycode", 0.7))
        reasons.append("Link uses punycode (possible lookalike domain).")
        reason_codes.append(ReasonCode.URL_PUNYCODE)

    if host and "." in host:
        tld = host.split(".")[-1]
        if tld in SUSPICIOUS_TLDS:
            signals.append(("suspicious_tld", 0.65))
            reasons.append(f"Domain ends with .{tld}, which is frequently abused.")
            reason_codes.append(ReasonCode.URL_SUSPICIOUS_TLD)

    debug = {"name": "url_checks", "host": host, "scheme": scheme}
    if not signals and u:
        signals.append(("no_strong_url_indicators", 0.45))
    return {"signals": signals, "reasons": reasons, "reason_codes": reason_codes, "debug": debug}
