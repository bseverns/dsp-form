from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from ..audio_features import AudioFeatures
from ..mesh.export import export_obj
from ..mesh.inspect import inspect_arrays
from ..utils import normalize, stable_seed, utc_now_iso, write_json


def ribbon_mesh(
    features: AudioFeatures,
    *,
    length_mm: float = 120.0,
    width_mm: float = 8.0,
    thickness_mm: float = 1.2,
    height_mm: float = 32.0,
    lateral_mm: float = 24.0,
    twist: float = 0.0,
    seed: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Create a rectangular swept ribbon following audio features.

    X = time
    Y = RMS / lateral movement
    Z = centroid / brightness
    onset = local thickness accent
    """
    rng = np.random.default_rng(stable_seed(seed))
    n = len(features.times)
    xs = np.linspace(-length_mm / 2, length_mm / 2, n)
    rms = normalize(features.rms)
    centroid = normalize(features.centroid)
    onset = normalize(features.onset)

    centers = []
    for i, x in enumerate(xs):
        wobble = (rng.random() - 0.5) * 0.25
        y = (rms[i] - 0.5) * lateral_mm + wobble
        z = centroid[i] * height_mm + 1.0
        centers.append((x, y, z))
    centers = np.asarray(centers, dtype=float)

    vertices = []
    faces: list[tuple[int, int, int]] = []
    for i, (x, y, z) in enumerate(centers):
        angle = twist * (i / max(n - 1, 1)) * np.pi * 2.0
        w = width_mm * (1.0 + onset[i] * 0.45)
        t = thickness_mm * (1.0 + onset[i] * 0.90)
        # Rotate width/thickness axes around X.
        cy, sy = np.cos(angle), np.sin(angle)
        width_vec = np.array([0.0, cy * w / 2, sy * w / 2])
        thick_vec = np.array([0.0, -sy * t / 2, cy * t / 2])
        center = np.array([x, y, z])
        vertices.extend(
            [
                center - width_vec - thick_vec,
                center + width_vec - thick_vec,
                center + width_vec + thick_vec,
                center - width_vec + thick_vec,
            ]
        )

    for i in range(n - 1):
        a = i * 4
        b = (i + 1) * 4
        # Connect corresponding rectangle corners into side faces.
        for j in range(4):
            j2 = (j + 1) % 4
            faces.extend([(a + j, b + j, b + j2), (a + j, b + j2, a + j2)])

    # Cap ends.
    faces.extend([(0, 1, 2), (0, 2, 3)])
    last = (n - 1) * 4
    faces.extend([(last, last + 2, last + 1), (last, last + 3, last + 2)])

    return np.asarray(vertices, dtype=float), np.asarray(faces, dtype=int)


def write_ribbon(
    features: AudioFeatures,
    out_path: str | Path,
    *,
    length_mm: float = 120.0,
    width_mm: float = 8.0,
    thickness_mm: float = 1.2,
    height_mm: float = 32.0,
    lateral_mm: float = 24.0,
    twist: float = 0.0,
    seed: int | None = None,
) -> dict[str, Any]:
    vertices, faces = ribbon_mesh(
        features,
        length_mm=length_mm,
        width_mm=width_mm,
        thickness_mm=thickness_mm,
        height_mm=height_mm,
        lateral_mm=lateral_mm,
        twist=twist,
        seed=seed,
    )
    obj_path = export_obj(vertices, faces, out_path)
    report = inspect_arrays(vertices, faces)
    manifest = {
        "created_utc": utc_now_iso(),
        "generator": "ribbon",
        "seed": seed,
        "parameters": {
            "length_mm": length_mm,
            "width_mm": width_mm,
            "thickness_mm": thickness_mm,
            "height_mm": height_mm,
            "lateral_mm": lateral_mm,
            "twist": twist,
        },
        "audio": features.to_manifest(),
        "mesh": report.to_dict(),
        "outputs": {"obj": str(obj_path)},
    }
    manifest_path = Path(out_path).with_suffix(".manifest.json")
    write_json(manifest_path, manifest)
    manifest["outputs"]["manifest"] = str(manifest_path)
    return manifest
