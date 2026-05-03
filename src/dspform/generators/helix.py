from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from ..audio_features import AudioFeatures
from ..mesh.export import export_obj
from ..mesh.inspect import inspect_arrays
from ..utils import normalize, runtime_provenance, stable_seed, utc_now_iso, write_json


def helix_mesh(
    features: AudioFeatures,
    *,
    height_mm: float = 120.0,
    base_radius_mm: float = 24.0,
    radial_amp_mm: float = 10.0,
    turns: float = 3.5,
    tube_radius_mm: float = 4.0,
    ridge_amp_mm: float = 1.6,
    angle_jitter_deg: float = 0.0,
    radius_noise_mm: float = 0.0,
    seed: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Create a signal-driven helical body.

    Time travels along a rising spiral instead of a flat axis or a pure ring.
    RMS and centroid modulate helix radius, onset thickens the tube, and
    bandwidth biases local twist.
    """
    frames = len(features.times)
    if frames < 4:
        raise ValueError("Need at least four audio frames to generate a helix.")

    rms = normalize(features.rms)
    centroid = normalize(features.centroid)
    onset = normalize(features.onset)
    bandwidth = normalize(features.bandwidth)

    rng = np.random.default_rng(stable_seed(seed))
    progress = np.linspace(0.0, 1.0, frames)
    angle_base = progress * turns * np.pi * 2.0
    angle_jitter_rad = np.deg2rad(angle_jitter_deg)
    angle_offsets = (rng.random(frames) - 0.5) * 2.0 * angle_jitter_rad if angle_jitter_deg > 0 else np.zeros(frames)

    helix_radius = (
        base_radius_mm
        + radial_amp_mm * (0.55 * rms + 0.30 * centroid + 0.15 * bandwidth - 0.5)
    )
    if radius_noise_mm > 0:
        helix_radius = helix_radius + ((rng.random(frames) - 0.5) * 2.0 * radius_noise_mm)
    helix_radius = np.maximum(helix_radius, tube_radius_mm * 1.25)

    z = progress * height_mm
    z = z + (centroid - 0.5) * (0.08 * height_mm) + (bandwidth - 0.5) * (0.03 * height_mm)
    angle = angle_base + angle_offsets

    centers = np.column_stack(
        [
            np.cos(angle) * helix_radius,
            np.sin(angle) * helix_radius,
            z,
        ]
    )

    tangents = _curve_tangents(centers)
    sides = 18
    vertices: list[tuple[float, float, float]] = []

    for i in range(frames):
        tangent = tangents[i]
        helper = np.array([0.0, 0.0, 1.0], dtype=float)
        if abs(float(np.dot(tangent, helper))) > 0.92:
            helper = np.array([0.0, 1.0, 0.0], dtype=float)
        normal = np.cross(helper, tangent)
        normal = normal / max(np.linalg.norm(normal), 1e-9)
        binormal = np.cross(tangent, normal)
        binormal = binormal / max(np.linalg.norm(binormal), 1e-9)

        # Bandwidth rotates the tube frame so rougher moments feel more torsional.
        twist_angle = (bandwidth[i] - 0.5) * np.pi * 0.9
        c = float(np.cos(twist_angle))
        s = float(np.sin(twist_angle))
        ring_u = (normal * c) + (binormal * s)
        ring_v = (-normal * s) + (binormal * c)

        ring_radius = tube_radius_mm + ridge_amp_mm * onset[i] + 0.8 * bandwidth[i]
        ring_radius = max(ring_radius, 0.8)
        center = centers[i]
        for side in range(sides):
            theta = (side / sides) * np.pi * 2.0
            offset = (ring_u * np.cos(theta) + ring_v * np.sin(theta)) * ring_radius
            point = center + offset
            vertices.append((float(point[0]), float(point[1]), float(point[2])))

    faces: list[tuple[int, int, int]] = []

    def idx(frame: int, side: int) -> int:
        return frame * sides + (side % sides)

    for frame in range(frames - 1):
        for side in range(sides):
            a = idx(frame, side)
            b = idx(frame, side + 1)
            c = idx(frame + 1, side + 1)
            d = idx(frame + 1, side)
            faces.append((a, b, c))
            faces.append((a, c, d))

    start_center_idx = len(vertices)
    start_center = centers[0]
    vertices.append((float(start_center[0]), float(start_center[1]), float(start_center[2])))
    for side in range(sides):
        faces.append((start_center_idx, idx(0, side), idx(0, side + 1)))

    end_center_idx = len(vertices)
    end_center = centers[-1]
    vertices.append((float(end_center[0]), float(end_center[1]), float(end_center[2])))
    end_frame = frames - 1
    for side in range(sides):
        faces.append((end_center_idx, idx(end_frame, side + 1), idx(end_frame, side)))

    return np.asarray(vertices, dtype=float), np.asarray(faces, dtype=int)


def _curve_tangents(points: np.ndarray) -> np.ndarray:
    tangents = np.zeros_like(points, dtype=float)
    tangents[0] = points[1] - points[0]
    tangents[-1] = points[-1] - points[-2]
    if len(points) > 2:
        tangents[1:-1] = points[2:] - points[:-2]
    norms = np.linalg.norm(tangents, axis=1, keepdims=True)
    return tangents / np.maximum(norms, 1e-9)


def write_helix(
    features: AudioFeatures,
    out_path: str | Path,
    *,
    height_mm: float = 120.0,
    base_radius_mm: float = 24.0,
    radial_amp_mm: float = 10.0,
    turns: float = 3.5,
    tube_radius_mm: float = 4.0,
    ridge_amp_mm: float = 1.6,
    angle_jitter_deg: float = 0.0,
    radius_noise_mm: float = 0.0,
    seed: int | None = None,
) -> dict[str, Any]:
    vertices, faces = helix_mesh(
        features,
        height_mm=height_mm,
        base_radius_mm=base_radius_mm,
        radial_amp_mm=radial_amp_mm,
        turns=turns,
        tube_radius_mm=tube_radius_mm,
        ridge_amp_mm=ridge_amp_mm,
        angle_jitter_deg=angle_jitter_deg,
        radius_noise_mm=radius_noise_mm,
        seed=seed,
    )
    obj_path = export_obj(vertices, faces, out_path)
    report = inspect_arrays(vertices, faces)
    manifest = {
        "created_utc": utc_now_iso(),
        "generator": "helix",
        "seed": seed,
        "parameters": {
            "height_mm": height_mm,
            "base_radius_mm": base_radius_mm,
            "radial_amp_mm": radial_amp_mm,
            "turns": turns,
            "tube_radius_mm": tube_radius_mm,
            "ridge_amp_mm": ridge_amp_mm,
            "angle_jitter_deg": angle_jitter_deg,
            "radius_noise_mm": radius_noise_mm,
        },
        "seed_usage": "geometry_rng" if (angle_jitter_deg > 0 or radius_noise_mm > 0) else "metadata_only",
        "audio": features.to_manifest(),
        "mesh": report.to_dict(),
        "provenance": runtime_provenance(),
        "outputs": {"obj": str(obj_path)},
    }
    manifest_path = Path(out_path).with_suffix(".manifest.json")
    write_json(manifest_path, manifest)
    manifest["outputs"]["manifest"] = str(manifest_path)
    return manifest
