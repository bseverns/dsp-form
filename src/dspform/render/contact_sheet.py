from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _record_title(index_payload: dict[str, Any], record: dict[str, Any]) -> str:
    if "param" in index_payload:
        return f"{index_payload['param']}={record.get('value')}"
    if "seed" in record:
        return f"seed={record['seed']}"
    return index_payload.get("generator", "preview")


def _record_summary(manifest: dict[str, Any]) -> str:
    mesh = manifest.get("mesh", {})
    structuresynth = manifest.get("structuresynth", {})
    if mesh:
        parts = [
            f"V {mesh.get('vertex_count', '-')}",
            f"F {mesh.get('face_count', '-')}",
        ]
        warnings = mesh.get("warnings", [])
        if warnings:
            parts.append(f"W {len(warnings)}")
        return " | ".join(parts)
    if structuresynth:
        template = structuresynth.get("template", "-")
        events = structuresynth.get("event_count_written", "-")
        return f"{template} | events {events}"
    return manifest.get("generator", "manifest")


def _normalize_mesh(mesh: Any) -> Any:
    import trimesh

    if isinstance(mesh, trimesh.Scene):
        return mesh.dump(concatenate=True)
    return mesh


def _draw_mesh_tile(ax: Any, obj_path: str | Path) -> None:
    import trimesh
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    mesh = _normalize_mesh(trimesh.load(obj_path, force="mesh", process=False))
    vertices = np.asarray(mesh.vertices, dtype=float)
    faces = np.asarray(mesh.faces, dtype=int)

    if len(vertices) == 0 or len(faces) == 0:
        raise ValueError(f"No renderable mesh data in {obj_path}")

    max_faces = 5000
    if len(faces) > max_faces:
        idx = np.linspace(0, len(faces) - 1, max_faces).astype(int)
        faces = faces[idx]

    tris = vertices[faces]
    poly = Poly3DCollection(
        tris,
        facecolor="#ccb183",
        edgecolor=(0.1, 0.08, 0.06, 0.10),
        linewidth=0.12,
        alpha=1.0,
    )
    ax.add_collection3d(poly)

    bounds_min = vertices.min(axis=0)
    bounds_max = vertices.max(axis=0)
    center = (bounds_min + bounds_max) / 2.0
    extent = float(np.max(bounds_max - bounds_min))
    radius = max(extent / 2.0, 1.0)

    ax.set_xlim(center[0] - radius, center[0] + radius)
    ax.set_ylim(center[1] - radius, center[1] + radius)
    ax.set_zlim(center[2] - radius, center[2] + radius)
    ax.view_init(elev=24, azim=36)
    ax.set_box_aspect((1, 1, 1))
    ax.set_axis_off()


def _draw_text_tile(ax: Any, title: str, summary: str, manifest: dict[str, Any]) -> None:
    ax.set_axis_off()
    ax.set_facecolor("#f3efe3")
    extra = []
    seed_usage = manifest.get("seed_usage")
    if seed_usage:
        extra.append(seed_usage)
    outputs = manifest.get("outputs", {})
    if outputs.get("eisenscript"):
        extra.append("grammar-only")
    text = "\n".join([title, summary] + extra)
    ax.text(
        0.5,
        0.5,
        text,
        ha="center",
        va="center",
        fontsize=10,
        family="monospace",
        color="#2f2418",
        transform=ax.transAxes,
    )


def build_contact_sheet(
    index_path: str | Path,
    out_path: str | Path,
    *,
    cols: int = 4,
    tile_width: float = 4.0,
    tile_height: float = 3.4,
) -> Path:
    import matplotlib.pyplot as plt

    index_payload = _load_json(index_path)
    records = index_payload.get("records", [])
    if not records:
        raise ValueError("Sweep index contains no records.")

    cols = max(1, int(cols))
    rows = int(math.ceil(len(records) / cols))
    fig = plt.figure(figsize=(cols * tile_width, rows * tile_height))

    title_bits = [index_payload.get("generator", "contact-sheet")]
    if "param" in index_payload:
        title_bits.append(str(index_payload["param"]))
    fig.suptitle(" | ".join(title_bits), fontsize=14, y=0.98)

    for idx, record in enumerate(records, start=1):
        manifest_path = record.get("manifest")
        manifest = _load_json(manifest_path) if manifest_path else {}
        title = _record_title(index_payload, record)
        summary = _record_summary(manifest)
        obj_path = record.get("obj")

        if obj_path:
            ax = fig.add_subplot(rows, cols, idx, projection="3d")
            try:
                _draw_mesh_tile(ax, obj_path)
            except Exception:
                fig.delaxes(ax)
                ax = fig.add_subplot(rows, cols, idx)
                _draw_text_tile(ax, title, summary, manifest)
            ax.set_title(title, fontsize=10, pad=8)
            ax.text2D(0.5, -0.06, summary, transform=ax.transAxes, ha="center", va="top", fontsize=8)
        else:
            ax = fig.add_subplot(rows, cols, idx)
            _draw_text_tile(ax, title, summary, manifest)

    for idx in range(len(records) + 1, rows * cols + 1):
        ax = fig.add_subplot(rows, cols, idx)
        ax.set_axis_off()

    output = Path(out_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(output, dpi=180, facecolor="#f7f1e3")
    plt.close(fig)
    return output
