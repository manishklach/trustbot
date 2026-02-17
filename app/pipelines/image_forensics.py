from __future__ import annotations

import base64
import io
import numpy as np
from PIL import Image
from typing import Dict, Any, List, Tuple
from app.models import ReasonCode

def _to_gray_np(img: Image.Image) -> np.ndarray:
    return np.asarray(img.convert("L"), dtype=np.float32)

def _blockiness(gray: np.ndarray, block: int = 8) -> float:
    h, w = gray.shape
    if h < block * 2 or w < block * 2:
        return 0.0
    v_edges = np.abs(gray[:, block::block] - gray[:, block-1::block]).mean()
    v_non = np.abs(gray[:, 1:] - gray[:, :-1]).mean()
    h_edges = np.abs(gray[block::block, :] - gray[block-1::block, :]).mean()
    h_non = np.abs(gray[1:, :] - gray[:-1, :]).mean()
    return float(((v_edges + h_edges) / 2.0) / (v_non + h_non + 1e-6))

def _edge_density(gray: np.ndarray) -> float:
    gx = np.abs(gray[:, 1:] - gray[:, :-1])
    gy = np.abs(gray[1:, :] - gray[:-1, :])
    g = 0.5 * (gx.mean() + gy.mean())
    return float(g / 255.0)

def analyze_image(image_b64: str) -> Dict[str, Any]:
    signals: List[Tuple[str, float]] = []
    reasons: List[str] = []
    reason_codes: List[ReasonCode] = []
    quality_penalty = 0.0

    if not image_b64:
        reasons.append("No image provided.")
        return {"signals": [("missing_image", 0.5)], "reasons": reasons, "reason_codes": reason_codes, "quality_penalty": 1.0, "debug": {"name": "image_forensics", "error": "missing"}}

    try:
        raw = base64.b64decode(image_b64)
        img = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as e:
        reasons.append("Could not decode the image.")
        return {"signals": [("decode_error", 0.5)], "reasons": reasons, "reason_codes": reason_codes, "quality_penalty": 1.0, "debug": {"name": "image_forensics", "error": str(e)}}

    gray = _to_gray_np(img)
    blk = _blockiness(gray)
    ed = _edge_density(gray)

    if blk > 1.35:
        signals.append(("heavy_compression", 0.6))
        reasons.append("Image shows strong compression artifacts; authenticity signals may be degraded.")
        reason_codes.append(ReasonCode.IMG_HEAVY_COMPRESSION)
        quality_penalty = max(quality_penalty, min(1.0, (blk - 1.35)))

    if ed > 0.08:
        signals.append(("textlike_edges", 0.55))
        reasons.append("Image has dense edges consistent with text-heavy screenshots (common for scam forwards).")
        reason_codes.append(ReasonCode.IMG_TEXTLIKE_EDGES)

    if ed < 0.02:
        signals.append(("low_signal", 0.5))
        reasons.append("Image has low detail; analysis may be uncertain.")
        reason_codes.append(ReasonCode.IMG_LOW_SIGNAL)
        quality_penalty = max(quality_penalty, 0.4)

    debug = {"name": "image_forensics", "blockiness": blk, "edge_density": ed, "size": img.size}
    if not signals:
        signals.append(("no_strong_image_indicators", 0.45))
    return {"signals": signals, "reasons": reasons, "reason_codes": reason_codes, "quality_penalty": float(quality_penalty), "debug": debug}
