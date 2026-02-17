from __future__ import annotations

import hashlib
import time
from typing import Optional, Dict, Any

_STORE: Dict[str, Dict[str, Any]] = {}
DEFAULT_TTL_SECONDS = 60 * 30

def _now() -> float:
    return time.time()

def put_ephemeral(key: str, payload: Dict[str, Any], ttl: int = DEFAULT_TTL_SECONDS) -> None:
    _STORE[key] = {"payload": payload, "expires": _now() + ttl}

def get_ephemeral(key: str) -> Optional[Dict[str, Any]]:
    item = _STORE.get(key)
    if not item:
        return None
    if item["expires"] < _now():
        _STORE.pop(key, None)
        return None
    return item["payload"]

def purge(key: str) -> bool:
    return _STORE.pop(key, None) is not None

def receipt_for_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()
