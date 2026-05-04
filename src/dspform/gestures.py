from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .audio_features import AudioFeatures
from .utils import normalize


@dataclass(frozen=True)
class Gesture:
    """A compact event derived from frame-level audio features."""

    frame: int
    time_seconds: float
    kind: str
    strength: float
    duration_frames: int
    brightness: float
    roughness: float


def extract_gestures(
    features: AudioFeatures,
    *,
    onset_threshold: float = 0.62,
    cluster_gap: int = 3,
) -> list[Gesture]:
    """Extract a small gesture/event layer from AudioFeatures.

    The intent is not semantic audio understanding. It is a practical middle
    layer between per-frame feature mapping and sculptural behavior.
    """
    frames = len(features.times)
    if frames == 0:
        return []
    if not 0.0 <= onset_threshold <= 1.0:
        raise ValueError("onset_threshold must be in [0, 1].")
    if cluster_gap < 0:
        raise ValueError("cluster_gap must be >= 0.")

    rms = normalize(features.rms)
    onset = normalize(features.onset)
    brightness = normalize(features.centroid)
    roughness = normalize(features.bandwidth)

    gestures: list[Gesture] = []
    onset_frames = np.flatnonzero(onset >= onset_threshold)
    for group in _group_indices(onset_frames, gap=cluster_gap):
        start = int(group[0])
        end = int(group[-1])
        local = onset[start : end + 1]
        peak_offset = int(np.argmax(local))
        peak_frame = start + peak_offset
        duration = end - start + 1
        strength = float(np.max(local))
        event_density = len(group) / max(duration, 1)
        if duration <= 2 and event_density >= 0.8:
            kind = "pulse"
        elif duration <= cluster_gap + 2:
            kind = "burst"
        else:
            kind = "cluster"
        gestures.append(
            Gesture(
                frame=peak_frame,
                time_seconds=float(features.times[peak_frame]),
                kind=kind,
                strength=strength,
                duration_frames=duration,
                brightness=float(brightness[peak_frame]),
                roughness=float(roughness[peak_frame]),
            )
        )

    silence_mask = (rms <= 0.10) & (onset <= onset_threshold * 0.35)
    min_silence = max(cluster_gap + 1, 3)
    for start, end in _true_runs(silence_mask, min_length=min_silence):
        frame = (start + end) // 2
        duration = end - start + 1
        gestures.append(
            Gesture(
                frame=frame,
                time_seconds=float(features.times[frame]),
                kind="silence",
                strength=float(1.0 - np.mean(rms[start : end + 1])),
                duration_frames=duration,
                brightness=float(np.mean(brightness[start : end + 1])),
                roughness=float(np.mean(roughness[start : end + 1])),
            )
        )

    return sorted(gestures, key=lambda item: (item.frame, item.kind))


def _group_indices(indices: np.ndarray, *, gap: int) -> list[np.ndarray]:
    if len(indices) == 0:
        return []
    groups: list[list[int]] = [[int(indices[0])]]
    for raw in indices[1:]:
        idx = int(raw)
        if idx - groups[-1][-1] <= gap + 1:
            groups[-1].append(idx)
        else:
            groups.append([idx])
    return [np.asarray(group, dtype=int) for group in groups]


def _true_runs(mask: np.ndarray, *, min_length: int) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for i, value in enumerate(mask):
        if bool(value) and start is None:
            start = i
        elif not bool(value) and start is not None:
            end = i - 1
            if end - start + 1 >= min_length:
                runs.append((start, end))
            start = None
    if start is not None:
        end = len(mask) - 1
        if end - start + 1 >= min_length:
            runs.append((start, end))
    return runs
