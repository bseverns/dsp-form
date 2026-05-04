from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from ..audio_features import AudioFeatures
from ..form_state import FormState
from ..gestures import Gesture, extract_gestures
from ..mesh.export import export_obj
from ..mesh.inspect import inspect_arrays
from ..utils import normalize, runtime_provenance, stable_seed, utc_now_iso, write_json


@dataclass(frozen=True)
class ProfileSettings:
    pull_mm: float
    lift_mm: float
    twist_gain: float
    scar_cut: float
    bloom_gain: float
    branch_gain: float
    heal_rate: float
    braid_amp: float


PROFILE_SETTINGS: dict[str, ProfileSettings] = {
    "scar": ProfileSettings(20.0, 18.0, 1.15, 1.00, 0.15, 0.45, 0.030, 0.10),
    "bloom": ProfileSettings(16.0, 24.0, 0.80, 0.25, 0.85, 0.90, 0.040, 0.08),
    "braid": ProfileSettings(18.0, 16.0, 1.75, 0.45, 0.25, 0.55, 0.032, 0.55),
    "faultline": ProfileSettings(28.0, 12.0, 1.30, 1.35, 0.05, 0.35, 0.025, 0.18),
    "organ": ProfileSettings(13.0, 28.0, 0.65, 0.20, 0.50, 0.25, 0.055, 0.06),
    "relic": ProfileSettings(12.0, 12.0, 0.95, 0.75, 0.10, 0.20, 0.018, 0.22),
}


def growth_body_mesh(
    features: AudioFeatures,
    *,
    profile: str = "scar",
    length_mm: float = 130.0,
    tube_radius_mm: float = 4.2,
    sides: int = 18,
    memory: float = 0.92,
    event_threshold: float = 0.62,
    branchiness: float = 0.25,
    scar_depth: float = 1.5,
    seed: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate a fossilized growth tube from audio behavior.

    RMS contributes growth pressure, centroid pulls the centerline, bandwidth
    twists the tube frame, onsets damage/scar the surface, and silence heals.
    """
    if profile not in PROFILE_SETTINGS:
        raise ValueError(f"Unknown profile: {profile}")
    frames = len(features.times)
    if frames < 4:
        raise ValueError("Need at least four audio frames to generate a growth body.")
    if sides < 6:
        raise ValueError("sides must be >= 6.")

    settings = PROFILE_SETTINGS[profile]
    branchiness = max(0.0, float(branchiness))
    scar_depth = max(0.0, float(scar_depth))
    rng = np.random.default_rng(stable_seed(seed))

    rms = normalize(features.rms)
    brightness = normalize(features.centroid)
    roughness = normalize(features.bandwidth)
    gestures = extract_gestures(features, onset_threshold=event_threshold)
    event_strength, silence_strength, scar_angles = _gesture_fields(gestures, frames=frames, rng=rng)

    centers = _centerline(
        rms=rms,
        brightness=brightness,
        roughness=roughness,
        event_strength=event_strength,
        silence_strength=silence_strength,
        length_mm=length_mm,
        memory=memory,
        settings=settings,
    )
    tangents = _curve_tangents(centers)

    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int]] = []
    state = FormState()
    twist_phase = 0.0
    ring_radii: list[float] = []
    ring_frames: list[tuple[np.ndarray, np.ndarray]] = []

    for frame in range(frames):
        state.update(
            energy=float(rms[frame]),
            event_strength=float(event_strength[frame]),
            brightness=float(brightness[frame]),
            roughness=float(roughness[frame]),
            silence=bool(silence_strength[frame] > 0.0),
            memory=memory,
            heal_rate=settings.heal_rate,
        )
        tangent = tangents[frame]
        normal, binormal = _frame_axes(tangent)
        twist_phase += (0.10 + state.roughness_memory * settings.twist_gain) * np.pi
        c = float(np.cos(twist_phase))
        s = float(np.sin(twist_phase))
        ring_u = (normal * c) + (binormal * s)
        ring_v = (-normal * s) + (binormal * c)
        ring_frames.append((ring_u, ring_v))

        base_radius = tube_radius_mm * (0.72 + 0.55 * state.growth_pressure + 0.20 * state.energy_memory)
        base_radius += settings.bloom_gain * scar_depth * event_strength[frame]
        base_radius *= 1.0 - (0.18 * silence_strength[frame])
        base_radius = max(base_radius, 0.9)
        ring_radii.append(base_radius)

        for side in range(sides):
            theta = (side / sides) * np.pi * 2.0
            angular_scar = _angular_lobe(theta, scar_angles[frame], width=0.48)
            braid = np.sin(theta * 3.0 + twist_phase) * settings.braid_amp * state.roughness_memory
            radius = base_radius * (1.0 + braid)
            wound = scar_depth * settings.scar_cut * (0.35 * state.damage_memory + 0.65 * event_strength[frame])
            radius -= wound * angular_scar
            radius = max(radius, 0.65)
            offset = (ring_u * np.cos(theta) + ring_v * np.sin(theta)) * radius
            point = centers[frame] + offset
            vertices.append((float(point[0]), float(point[1]), float(point[2])))

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

    _cap_tube(vertices, faces, centers, sides)
    _add_event_branches(
        vertices,
        faces,
        centers=centers,
        ring_frames=ring_frames,
        ring_radii=ring_radii,
        gestures=gestures,
        sides=sides,
        branchiness=branchiness * settings.branch_gain,
        scar_depth=scar_depth,
        rng=rng,
    )

    return np.asarray(vertices, dtype=float), np.asarray(faces, dtype=int)


def write_growth_body(
    features: AudioFeatures,
    out_path: str | Path,
    *,
    profile: str = "scar",
    length_mm: float = 130.0,
    tube_radius_mm: float = 4.2,
    sides: int = 18,
    memory: float = 0.92,
    event_threshold: float = 0.62,
    branchiness: float = 0.25,
    scar_depth: float = 1.5,
    seed: int | None = None,
) -> dict[str, Any]:
    gestures = extract_gestures(features, onset_threshold=event_threshold)
    vertices, faces = growth_body_mesh(
        features,
        profile=profile,
        length_mm=length_mm,
        tube_radius_mm=tube_radius_mm,
        sides=sides,
        memory=memory,
        event_threshold=event_threshold,
        branchiness=branchiness,
        scar_depth=scar_depth,
        seed=seed,
    )
    obj_path = export_obj(vertices, faces, out_path)
    report = inspect_arrays(vertices, faces)
    manifest_path = Path(out_path).with_suffix(".manifest.json")
    manifest = {
        "created_utc": utc_now_iso(),
        "generator": "growth_body",
        "seed": seed,
        "parameters": {
            "profile": profile,
            "length_mm": length_mm,
            "tube_radius_mm": tube_radius_mm,
            "sides": sides,
            "memory": memory,
            "event_threshold": event_threshold,
            "branchiness": branchiness,
            "scar_depth": scar_depth,
        },
        "seed_usage": "geometry_rng",
        "audio": features.to_manifest(),
        "gestures": _gesture_summary(gestures),
        "mesh": report.to_dict(),
        "provenance": runtime_provenance(),
        "outputs": {"obj": str(obj_path), "manifest": str(manifest_path)},
    }
    write_json(manifest_path, manifest)
    return manifest


def _gesture_fields(
    gestures: list[Gesture],
    *,
    frames: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    event_strength = np.zeros(frames, dtype=float)
    silence_strength = np.zeros(frames, dtype=float)
    scar_angles = rng.random(frames) * np.pi * 2.0
    current_angle = float(rng.random() * np.pi * 2.0)
    for gesture in gestures:
        half = max(gesture.duration_frames // 2, 1)
        start = max(0, gesture.frame - half)
        end = min(frames - 1, gesture.frame + half)
        weights = np.hanning(max(end - start + 3, 3))[1:-1]
        if len(weights) != end - start + 1:
            weights = np.ones(end - start + 1, dtype=float)
        if gesture.kind == "silence":
            silence_strength[start : end + 1] = np.maximum(
                silence_strength[start : end + 1],
                weights * gesture.strength,
            )
        else:
            current_angle += (gesture.roughness - 0.5) * np.pi + float(rng.normal(0.0, 0.25))
            event_strength[start : end + 1] = np.maximum(
                event_strength[start : end + 1],
                weights * gesture.strength,
            )
            scar_angles[start : end + 1] = current_angle
    return event_strength, silence_strength, scar_angles


def _centerline(
    *,
    rms: np.ndarray,
    brightness: np.ndarray,
    roughness: np.ndarray,
    event_strength: np.ndarray,
    silence_strength: np.ndarray,
    length_mm: float,
    memory: float,
    settings: ProfileSettings,
) -> np.ndarray:
    frames = len(rms)
    state = FormState()
    centers = np.zeros((frames, 3), dtype=float)
    step_base = length_mm / max(frames - 1, 1)
    sway = 0.0
    lift = 0.0
    torsion = 0.0
    for frame in range(1, frames):
        state.update(
            energy=float(rms[frame]),
            event_strength=float(event_strength[frame]),
            brightness=float(brightness[frame]),
            roughness=float(roughness[frame]),
            silence=bool(silence_strength[frame] > 0.0),
            memory=memory,
            heal_rate=settings.heal_rate,
        )
        torsion += (roughness[frame] - 0.35) * settings.twist_gain * 0.16
        sway += (state.brightness_memory - 0.5) * settings.pull_mm * 0.015
        lift += (state.energy_memory - 0.35) * settings.lift_mm * 0.012
        heal = silence_strength[frame]
        sway *= 1.0 - (0.12 * heal)
        lift *= 1.0 - (0.08 * heal)

        step = step_base * (0.72 + state.growth_pressure * 1.15)
        direction = np.array(
            [
                1.0,
                np.sin(torsion) * 0.25 + sway * 0.018,
                np.cos(torsion * 0.7) * 0.10 + lift * 0.018,
            ],
            dtype=float,
        )
        direction /= max(np.linalg.norm(direction), 1e-9)
        centers[frame] = centers[frame - 1] + direction * step

    centers[:, 0] -= np.mean(centers[:, 0])
    centers[:, 1] -= np.mean(centers[:, 1])
    centers[:, 2] -= np.min(centers[:, 2])
    return centers


def _curve_tangents(points: np.ndarray) -> np.ndarray:
    tangents = np.zeros_like(points, dtype=float)
    tangents[0] = points[1] - points[0]
    tangents[-1] = points[-1] - points[-2]
    if len(points) > 2:
        tangents[1:-1] = points[2:] - points[:-2]
    norms = np.linalg.norm(tangents, axis=1, keepdims=True)
    return tangents / np.maximum(norms, 1e-9)


def _frame_axes(tangent: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    helper = np.array([0.0, 0.0, 1.0], dtype=float)
    if abs(float(np.dot(tangent, helper))) > 0.90:
        helper = np.array([0.0, 1.0, 0.0], dtype=float)
    normal = np.cross(helper, tangent)
    normal /= max(np.linalg.norm(normal), 1e-9)
    binormal = np.cross(tangent, normal)
    binormal /= max(np.linalg.norm(binormal), 1e-9)
    return normal, binormal


def _angular_lobe(theta: float, center: float, *, width: float) -> float:
    delta = np.angle(np.exp(1j * (theta - center)))
    return float(np.exp(-0.5 * (delta / width) ** 2))


def _cap_tube(
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, int, int]],
    centers: np.ndarray,
    sides: int,
) -> None:
    start_center_idx = len(vertices)
    start = centers[0]
    vertices.append((float(start[0]), float(start[1]), float(start[2])))
    for side in range(sides):
        faces.append((start_center_idx, side, (side + 1) % sides))

    end_center_idx = len(vertices)
    end = centers[-1]
    vertices.append((float(end[0]), float(end[1]), float(end[2])))
    base = (len(centers) - 1) * sides
    for side in range(sides):
        faces.append((end_center_idx, base + ((side + 1) % sides), base + side))


def _add_event_branches(
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, int, int]],
    *,
    centers: np.ndarray,
    ring_frames: list[tuple[np.ndarray, np.ndarray]],
    ring_radii: list[float],
    gestures: list[Gesture],
    sides: int,
    branchiness: float,
    scar_depth: float,
    rng: np.random.Generator,
) -> None:
    if branchiness <= 0:
        return
    for gesture in gestures:
        if gesture.kind == "silence" or gesture.frame <= 0 or gesture.frame >= len(centers) - 1:
            continue
        if rng.random() > min(1.0, branchiness * gesture.strength):
            continue
        frame = gesture.frame
        ring_u, ring_v = ring_frames[frame]
        theta = float(rng.random() * np.pi * 2.0)
        radial = ring_u * np.cos(theta) + ring_v * np.sin(theta)
        base_center = centers[frame] + radial * ring_radii[frame] * 0.92
        branch_length = (5.0 + 10.0 * gesture.strength) * max(branchiness, 0.15)
        branch_radius = max(0.55, min(ring_radii[frame] * 0.42, 0.9 + scar_depth * 0.18))
        tip = base_center + radial * branch_length + np.array([0.0, 0.0, branch_length * 0.18])
        start_idx = len(vertices)
        branch_sides = max(6, min(10, sides // 2))
        tangent = tip - base_center
        tangent /= max(np.linalg.norm(tangent), 1e-9)
        normal, binormal = _frame_axes(tangent)
        for side in range(branch_sides):
            angle = (side / branch_sides) * np.pi * 2.0
            point = base_center + (normal * np.cos(angle) + binormal * np.sin(angle)) * branch_radius
            vertices.append((float(point[0]), float(point[1]), float(point[2])))
        tip_idx = len(vertices)
        vertices.append((float(tip[0]), float(tip[1]), float(tip[2])))
        for side in range(branch_sides):
            faces.append((start_idx + side, start_idx + ((side + 1) % branch_sides), tip_idx))


def _gesture_summary(gestures: list[Gesture]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for gesture in gestures:
        counts[gesture.kind] = counts.get(gesture.kind, 0) + 1
    return {
        "count": len(gestures),
        "kinds": counts,
        "first_events": [
            {
                "frame": gesture.frame,
                "time_seconds": round(gesture.time_seconds, 6),
                "kind": gesture.kind,
                "strength": round(gesture.strength, 6),
                "duration_frames": gesture.duration_frames,
                "brightness": round(gesture.brightness, 6),
                "roughness": round(gesture.roughness, 6),
            }
            for gesture in gestures[:16]
        ],
    }
