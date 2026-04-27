from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


def ensure_parent(path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def normalize(values: np.ndarray, eps: float = 1e-9) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    lo = np.nanmin(arr)
    hi = np.nanmax(arr)
    if hi - lo < eps:
        return np.zeros_like(arr)
    return (arr - lo) / (hi - lo)


def write_json(path: str | Path, payload: dict[str, Any]) -> Path:
    p = ensure_parent(path)
    p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return p


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def stable_seed(seed: int | None) -> int:
    if seed is None:
        return 0
    return int(seed) % (2**32 - 1)
