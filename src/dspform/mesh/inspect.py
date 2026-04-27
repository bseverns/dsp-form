from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass
class MeshReport:
    vertex_count: int
    face_count: int
    bounds_min: list[float]
    bounds_max: list[float]
    extents: list[float]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "vertex_count": self.vertex_count,
            "face_count": self.face_count,
            "bounds_min": self.bounds_min,
            "bounds_max": self.bounds_max,
            "extents": self.extents,
            "warnings": self.warnings,
        }


def inspect_arrays(vertices: np.ndarray, faces: np.ndarray) -> MeshReport:
    vertices = np.asarray(vertices, dtype=float)
    faces = np.asarray(faces, dtype=int)
    warnings: list[str] = []

    if vertices.size == 0:
        warnings.append("No vertices found.")
        bounds_min = bounds_max = extents = [0.0, 0.0, 0.0]
    else:
        bounds_min_np = vertices.min(axis=0)
        bounds_max_np = vertices.max(axis=0)
        extents_np = bounds_max_np - bounds_min_np
        bounds_min = bounds_min_np.round(6).tolist()
        bounds_max = bounds_max_np.round(6).tolist()
        extents = extents_np.round(6).tolist()
        if np.any(extents_np <= 0):
            warnings.append("One or more mesh extents are zero; form may be flat or invalid for printing.")

    if faces.size == 0:
        warnings.append("No faces found.")
    elif faces.min() < 0 or faces.max() >= len(vertices):
        warnings.append("Face indices reference vertices outside the vertex array.")

    return MeshReport(
        vertex_count=int(len(vertices)),
        face_count=int(len(faces)),
        bounds_min=bounds_min,
        bounds_max=bounds_max,
        extents=extents,
        warnings=warnings,
    )


def inspect_with_trimesh(path: str | Path) -> dict[str, Any]:
    """Load a mesh through trimesh and return printable-health hints."""
    import trimesh

    mesh = trimesh.load_mesh(Path(path), process=False)
    return {
        "path": str(path),
        "is_watertight": bool(getattr(mesh, "is_watertight", False)),
        "is_winding_consistent": bool(getattr(mesh, "is_winding_consistent", False)),
        "euler_number": int(getattr(mesh, "euler_number", 0)),
        "volume": float(getattr(mesh, "volume", 0.0)) if getattr(mesh, "is_volume", False) else None,
        "area": float(getattr(mesh, "area", 0.0)),
        "bounds": np.asarray(mesh.bounds).round(6).tolist() if hasattr(mesh, "bounds") else None,
    }
