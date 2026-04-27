from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from ..audio_features import AudioFeatures
from ..mesh.export import export_obj
from ..mesh.inspect import inspect_arrays
from ..utils import normalize, utc_now_iso, write_json


def vessel_mesh(
    features: AudioFeatures,
    *,
    height_mm: float = 90.0,
    base_radius_mm: float = 20.0,
    radial_amp_mm: float = 12.0,
    layers: int = 48,
    ridge_amp_mm: float = 3.0,
    close_top: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """Create a circular vessel from audio features.

    Angle = time frame
    Height = vertical layer
    Radius = RMS + spectral centroid + onset ridge energy
    """
    frames = len(features.times)
    if frames < 4:
        raise ValueError("Need at least four audio frames to generate a vessel.")

    rms = normalize(features.rms)
    centroid = normalize(features.centroid)
    onset = normalize(features.onset)
    bandwidth = normalize(features.bandwidth)

    vertices = []
    for layer in range(layers):
        v = layer / max(layers - 1, 1)
        z = v * height_mm
        layer_shape = np.sin(v * np.pi)  # quiet at base and lip, louder at belly
        for i in range(frames):
            a = (i / frames) * np.pi * 2.0
            ridge = np.sin(v * np.pi * 12.0 + onset[i] * np.pi) * ridge_amp_mm * onset[i]
            radius = (
                base_radius_mm
                + radial_amp_mm * rms[i] * layer_shape
                + 5.0 * (centroid[i] - 0.5) * layer_shape
                + 3.0 * bandwidth[i] * np.sin(v * np.pi * 2.0)
                + ridge
            )
            x = np.cos(a) * radius
            y = np.sin(a) * radius
            vertices.append((x, y, z))

    faces: list[tuple[int, int, int]] = []

    def idx(layer: int, frame: int) -> int:
        return layer * frames + (frame % frames)

    for layer in range(layers - 1):
        for i in range(frames):
            a = idx(layer, i)
            b = idx(layer, i + 1)
            c = idx(layer + 1, i + 1)
            d = idx(layer + 1, i)
            faces.append((a, b, c))
            faces.append((a, c, d))

    # Bottom cap.
    bottom_center = len(vertices)
    vertices.append((0.0, 0.0, 0.0))
    for i in range(frames):
        faces.append((bottom_center, idx(0, i + 1), idx(0, i)))

    if close_top:
        top_center = len(vertices)
        vertices.append((0.0, 0.0, height_mm))
        top_layer = layers - 1
        for i in range(frames):
            faces.append((top_center, idx(top_layer, i), idx(top_layer, i + 1)))

    return np.asarray(vertices, dtype=float), np.asarray(faces, dtype=int)


def write_vessel(
    features: AudioFeatures,
    out_path: str | Path,
    *,
    height_mm: float = 90.0,
    base_radius_mm: float = 20.0,
    radial_amp_mm: float = 12.0,
    layers: int = 48,
    ridge_amp_mm: float = 3.0,
    close_top: bool = False,
    seed: int | None = None,
) -> dict[str, Any]:
    vertices, faces = vessel_mesh(
        features,
        height_mm=height_mm,
        base_radius_mm=base_radius_mm,
        radial_amp_mm=radial_amp_mm,
        layers=layers,
        ridge_amp_mm=ridge_amp_mm,
        close_top=close_top,
    )
    obj_path = export_obj(vertices, faces, out_path)
    report = inspect_arrays(vertices, faces)
    manifest = {
        "created_utc": utc_now_iso(),
        "generator": "vessel",
        "seed": seed,
        "parameters": {
            "height_mm": height_mm,
            "base_radius_mm": base_radius_mm,
            "radial_amp_mm": radial_amp_mm,
            "layers": layers,
            "ridge_amp_mm": ridge_amp_mm,
            "close_top": close_top,
        },
        "audio": features.to_manifest(),
        "mesh": report.to_dict(),
        "outputs": {"obj": str(obj_path)},
    }
    manifest_path = Path(out_path).with_suffix(".manifest.json")
    write_json(manifest_path, manifest)
    manifest["outputs"]["manifest"] = str(manifest_path)
    return manifest
