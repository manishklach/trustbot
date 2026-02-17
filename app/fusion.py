from __future__ import annotations

from typing import Dict, Any, List, Tuple
from app.models import Verdict

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def fuse(signals: List[Tuple[str, float]], quality_penalty: float = 0.0) -> Dict[str, Any]:
    if not signals:
        base = 0.5
    else:
        base = sum(s for _, s in signals) / len(signals)

    ambiguity = 1.0 - abs(base - 0.5) * 2.0
    conf = clamp01(1.0 - 0.65 * ambiguity - 0.5 * quality_penalty)

    if conf < 0.45:
        verdict = Verdict.UNSURE
    else:
        if base >= 0.65:
            verdict = Verdict.RISKY
        elif base <= 0.35:
            verdict = Verdict.SAFE
        else:
            verdict = Verdict.UNSURE

    return {"risk": base, "confidence": conf, "verdict": verdict}
