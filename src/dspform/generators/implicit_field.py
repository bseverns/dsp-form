from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from ..audio_features import AudioFeatures
from ..mesh.export import export_obj
from ..mesh.inspect import inspect_arrays
from ..utils import normalize, utc_now_iso, write_json


@dataclass
class FieldSettings:
    resolution: int = 48
    level: float = 0.35
    radius: float = 1.0


def feature_field(features: AudioFeatures, settings: FieldSettings = FieldSettings()) -> np.ndarray:
    """Create a starter 3D scalar field from audio features.

    This is intentionally modest. Treat it as a sketch pad for marching cubes:
    RMS creates central density, centroid shifts the density upward, onset adds
    local hot spots along the time axis.
    """
    n = settings.resolution
    coords = np.linspace(-1.0, 1.0, n)
    x, y, z = np.meshgrid(coords, coords, coords, indexing="ij")
    field = np.zeros((n, n, n), dtype=float)

    rms = normalize(features.rms)
    centroid = normalize(features.centroid)
    onset = normalize(features.onset)
    frame_count = len(rms)

    for i in range(0, frame_count, max(1, frame_count // 32)):
        t = i / max(frame_count - 1, 1)
        cx = -0.8 + 1.6 * t
        cy = 0.25 * np.sin(t * np.pi * 4.0)
        cz = -0.25 + 0.5 * centroid[i]
        amp = 0.2 + 0.8 * rms[i] + 0.5 * onset[i]
        sigma = 0.10 + 0.08 * rms[i]
        field += amp * np.exp(-((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2) / (2 * sigma**2))

    return normalize(field)


def marching_cubes_mesh(field: np.ndarray, *, level: float = 0.35, scale_mm: float = 80.0) -> tuple[np.ndarray, np.ndarray]:
    from skimage import measure

    verts, faces, _normals, _values = measure.marching_cubes(field, level=level)
    verts = verts / max(field.shape) * scale_mm
    verts -= verts.mean(axis=0)
    return np.asarray(verts, dtype=float), np.asarray(faces, dtype=int)


def write_implicit_field(
    features: AudioFeatures,
    out_path: str | Path,
    *,
    resolution: int = 48,
    level: float = 0.35,
    scale_mm: float = 80.0,
    seed: int | None = None,
) -> dict[str, Any]:
    settings = FieldSettings(resolution=resolution, level=level)
    field = feature_field(features, settings)
    vertices, faces = marching_cubes_mesh(field, level=level, scale_mm=scale_mm)
    obj_path = export_obj(vertices, faces, out_path)
    report = inspect_arrays(vertices, faces)
    manifest = {
        "created_utc": utc_now_iso(),
        "generator": "implicit_field",
        "seed": seed,
        "parameters": {"resolution": resolution, "level": level, "scale_mm": scale_mm},
        "audio": features.to_manifest(),
        "mesh": report.to_dict(),
        "outputs": {"obj": str(obj_path)},
    }
    manifest_path = Path(out_path).with_suffix(".manifest.json")
    write_json(manifest_path, manifest)
    manifest["outputs"]["manifest"] = str(manifest_path)
    return manifest
