from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from ..audio_features import AudioFeatures
from ..mesh.export import export_obj
from ..mesh.inspect import inspect_arrays
from ..utils import normalize, utc_now_iso, write_json


def terrain_mesh(
    features: AudioFeatures,
    *,
    width_mm: float = 90.0,
    depth_mm: float = 60.0,
    height_mm: float = 14.0,
    base_mm: float = 2.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Create a watertight-ish spectrogram relief tile.

    X = time
    Y = frequency-bin index
    Z = spectrogram energy plus base
    """
    grid = normalize(features.spectrogram_db)
    rows, cols = grid.shape

    xs = np.linspace(-width_mm / 2, width_mm / 2, cols)
    ys = np.linspace(-depth_mm / 2, depth_mm / 2, rows)

    top_vertices = []
    bottom_vertices = []
    for yi, y in enumerate(ys):
        for xi, x in enumerate(xs):
            z = base_mm + float(grid[yi, xi]) * height_mm
            top_vertices.append((x, y, z))
            bottom_vertices.append((x, y, 0.0))

    vertices = np.asarray(top_vertices + bottom_vertices, dtype=float)
    faces: list[tuple[int, int, int]] = []

    def top_idx(r: int, c: int) -> int:
        return r * cols + c

    def bottom_idx(r: int, c: int) -> int:
        return rows * cols + r * cols + c

    # Top and bottom faces.
    for r in range(rows - 1):
        for c in range(cols - 1):
            a = top_idx(r, c)
            b = top_idx(r, c + 1)
            c2 = top_idx(r + 1, c + 1)
            d = top_idx(r + 1, c)
            faces.append((a, b, c2))
            faces.append((a, c2, d))

            ba = bottom_idx(r, c)
            bb = bottom_idx(r, c + 1)
            bc = bottom_idx(r + 1, c + 1)
            bd = bottom_idx(r + 1, c)
            faces.append((ba, bc, bb))
            faces.append((ba, bd, bc))

    # Side walls: front/back rows and left/right columns.
    for c in range(cols - 1):
        # low row
        faces.extend(_quad_to_triangles(top_idx(0, c), top_idx(0, c + 1), bottom_idx(0, c + 1), bottom_idx(0, c)))
        # high row
        faces.extend(_quad_to_triangles(top_idx(rows - 1, c + 1), top_idx(rows - 1, c), bottom_idx(rows - 1, c), bottom_idx(rows - 1, c + 1)))

    for r in range(rows - 1):
        # left col
        faces.extend(_quad_to_triangles(top_idx(r + 1, 0), top_idx(r, 0), bottom_idx(r, 0), bottom_idx(r + 1, 0)))
        # right col
        faces.extend(_quad_to_triangles(top_idx(r, cols - 1), top_idx(r + 1, cols - 1), bottom_idx(r + 1, cols - 1), bottom_idx(r, cols - 1)))

    return vertices, np.asarray(faces, dtype=int)


def _quad_to_triangles(a: int, b: int, c: int, d: int) -> list[tuple[int, int, int]]:
    return [(a, b, c), (a, c, d)]


def write_terrain(
    features: AudioFeatures,
    out_path: str | Path,
    *,
    width_mm: float = 90.0,
    depth_mm: float = 60.0,
    height_mm: float = 14.0,
    base_mm: float = 2.0,
    seed: int | None = None,
) -> dict[str, Any]:
    vertices, faces = terrain_mesh(
        features,
        width_mm=width_mm,
        depth_mm=depth_mm,
        height_mm=height_mm,
        base_mm=base_mm,
    )
    obj_path = export_obj(vertices, faces, out_path)
    report = inspect_arrays(vertices, faces)
    manifest = {
        "created_utc": utc_now_iso(),
        "generator": "terrain",
        "seed": seed,
        "parameters": {
            "width_mm": width_mm,
            "depth_mm": depth_mm,
            "height_mm": height_mm,
            "base_mm": base_mm,
        },
        "audio": features.to_manifest(),
        "mesh": report.to_dict(),
        "outputs": {"obj": str(obj_path)},
    }
    manifest_path = Path(out_path).with_suffix(".manifest.json")
    write_json(manifest_path, manifest)
    manifest["outputs"]["manifest"] = str(manifest_path)
    return manifest
