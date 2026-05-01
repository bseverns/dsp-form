from __future__ import annotations

import json
import platform
import subprocess
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


def _package_versions(names: list[str]) -> dict[str, str]:
    try:
        import importlib.metadata as importlib_metadata
    except Exception:
        return {}

    versions: dict[str, str] = {}
    for name in names:
        try:
            versions[name] = importlib_metadata.version(name)
        except Exception:
            continue
    return versions


def _git_commit_short() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return out or None
    except Exception:
        return None


def runtime_provenance() -> dict[str, Any]:
    payload: dict[str, Any] = {
        "python_version": platform.python_version(),
        "package_versions": _package_versions(
            [
                "dsp-form-lab",
                "numpy",
                "scipy",
                "librosa",
                "soundfile",
                "trimesh",
                "scikit-image",
                "matplotlib",
            ]
        ),
    }
    git_sha = _git_commit_short()
    if git_sha:
        payload["git_commit"] = git_sha
    return payload
