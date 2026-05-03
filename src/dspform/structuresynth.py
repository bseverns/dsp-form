from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from .audio_features import AudioFeatures
from .utils import ensure_parent, normalize, runtime_provenance, stable_seed, utc_now_iso, write_json


STRUCTURESYTH_TEMPLATES = {"onset-lattice", "radial-burst", "helix-coil", "helix-thread", "helix-vine", "chrono-body", "chrono-body-dense"}


def _safe_float(value: float, *, digits: int = 3) -> str:
    """Format floats compactly for EisenScript output."""
    return f"{float(value):.{digits}f}".rstrip("0").rstrip(".")


def _local_peaks(values: np.ndarray, *, threshold: float, max_events: int) -> list[int]:
    """Return local peak frame indices above threshold, sorted by time.

    This is intentionally small and dependency-free. It is not meant to replace
    a full onset picker; it just turns an onset envelope into a manageable set
    of StructureSynth growth calls.
    """
    arr = np.asarray(values, dtype=float)
    if len(arr) == 0:
        return []
    peaks: list[int] = []
    for idx in range(1, len(arr) - 1):
        if arr[idx] >= threshold and arr[idx] >= arr[idx - 1] and arr[idx] >= arr[idx + 1]:
            peaks.append(idx)
    if not peaks:
        peaks = [int(np.argmax(arr))]
    if len(peaks) > max_events:
        # Keep the strongest peaks, then restore chronological order.
        strongest = sorted(peaks, key=lambda i: arr[i], reverse=True)[:max_events]
        peaks = sorted(strongest)
    return peaks


def summarize_for_structuresynth(features: AudioFeatures, *, onset_threshold: float = 0.62) -> dict[str, Any]:
    """Summarize audio features into grammar-level controls."""
    rms = normalize(features.rms)
    centroid = normalize(features.centroid)
    bandwidth = normalize(features.bandwidth)
    onset = normalize(features.onset)

    frame_count = max(1, len(features.times))
    peak_indices = _local_peaks(onset, threshold=onset_threshold, max_events=64)
    onset_density = min(1.0, len(peak_indices) / max(1, frame_count / 8.0))

    return {
        "rms_mean": float(np.mean(rms)) if len(rms) else 0.0,
        "rms_max": float(np.max(rms)) if len(rms) else 0.0,
        "centroid_mean": float(np.mean(centroid)) if len(centroid) else 0.0,
        "bandwidth_mean": float(np.mean(bandwidth)) if len(bandwidth) else 0.0,
        "onset_mean": float(np.mean(onset)) if len(onset) else 0.0,
        "onset_max": float(np.max(onset)) if len(onset) else 0.0,
        "onset_threshold": float(onset_threshold),
        "onset_count": int(len(peak_indices)),
        "onset_density": float(onset_density),
        "frame_count": int(frame_count),
        "peak_indices": [int(i) for i in peak_indices],
    }


def _control_indices(frame_count: int, peaks: list[int], *, minimum: int = 8, maximum: int = 14) -> list[int]:
    """Blend evenly spaced control frames with event peaks for connected grammars."""
    if frame_count <= 0:
        return []
    sample_count = max(minimum, min(maximum, frame_count // 24 if frame_count >= 24 else minimum))
    evenly_spaced = np.linspace(0, frame_count - 1, sample_count).astype(int).tolist()
    return sorted(set(evenly_spaced + [int(i) for i in peaks]))


def generate_eisenscript(
    features: AudioFeatures,
    *,
    seed: int = 0,
    template: str = "onset-lattice",
    max_events: int = 24,
    onset_threshold: float = 0.62,
) -> tuple[str, dict[str, Any]]:
    """Generate a StructureSynth/EisenScript grammar from audio features.

    The current template uses the captured WAV as a *score* for recursive
    growth. RMS controls scale, onset peaks instantiate event nodes, centroid
    chooses low/mid/high rule families, and bandwidth controls spread.
    """
    if template not in STRUCTURESYTH_TEMPLATES:
        allowed = ", ".join(sorted(STRUCTURESYTH_TEMPLATES))
        raise ValueError(f"Only templates {{{allowed}}} are implemented in this starter repo.")

    rng_seed = stable_seed(seed)
    summary = summarize_for_structuresynth(features, onset_threshold=onset_threshold)
    rms = normalize(features.rms)
    centroid = normalize(features.centroid)
    bandwidth = normalize(features.bandwidth)
    onset = normalize(features.onset)

    peaks = _local_peaks(onset, threshold=onset_threshold, max_events=max_events)
    if len(peaks) == 0 and len(onset) > 0:
        peaks = [int(np.argmax(onset))]

    energy = summary["rms_mean"]
    brightness = summary["centroid_mean"]
    roughness = summary["bandwidth_mean"]
    density = summary["onset_density"]

    maxdepth = int(20 + 18 * energy + 10 * density)
    maxobjects = int(900 + 4500 * density + 1600 * roughness)
    trunk_scale = 0.75 + 1.2 * energy
    trunk_step = 0.7 + 0.6 * energy
    trunk_decay = 0.965 - 0.05 * roughness
    branch_angle = 10 + 42 * brightness
    twist = 6 + 80 * roughness
    branch_decay = 0.72 + 0.16 * (1.0 - roughness)
    detail_scale = 0.14 + 0.38 * max(0.05, brightness)

    if template == "chrono-body-dense":
        maxdepth = int(24 + 10 * energy + 16 * density)
        maxobjects = int(1800 + 3400 * density + 2600 * roughness)
        body_scale = 0.84 + 0.88 * energy
        body_decay = 0.93 - 0.03 * roughness
        spine_step = 0.18 + 0.12 * energy
        turn_base = 8.0 + 26.0 * roughness
        pitch_base = 5.0 + 12.0 * brightness
        lateral_base = 0.05 + 0.12 * brightness
        control_points = _control_indices(len(features.times), peaks, minimum=22, maximum=30)
        peak_set = set(peaks)

        lines: list[str] = []
        lines.extend(
            [
                "/*",
                "  Generated by dsp-form-lab.",
                "  StructureSynth lane: chrono-body-dense template.",
                "  A denser chronological body with tighter spacing and closer motif attachment.",
                "*/",
                f"set seed {rng_seed}",
                f"set maxdepth {maxdepth}",
                f"set maxobjects {maxobjects}",
                "set background white",
                "start",
                "",
                "rule start {",
                f"  {{ s {_safe_float(body_scale)} }} chronod0",
                "}",
                "",
            ]
        )

        duration = max(features.duration_seconds, 1e-6)
        chrono_rule_names = [f"chronod{i}" for i in range(len(control_points))] or ["chronod0"]
        motif_cycle = ("ribbonFin", "vesselBud", "helixHook", "terrainRidge")

        for control_number, idx in enumerate(control_points):
            e = float(rms[idx]) if idx < len(rms) else energy
            c = float(centroid[idx]) if idx < len(centroid) else brightness
            b = float(bandwidth[idx]) if idx < len(bandwidth) else roughness
            o = float(onset[idx]) if idx < len(onset) else 0.0
            t_norm = float(features.times[idx] / duration) if idx < len(features.times) else 0.0

            current_rule = chrono_rule_names[control_number]
            next_rule = chrono_rule_names[control_number + 1] if control_number + 1 < len(chrono_rule_names) else "chronodTail"

            step = spine_step + 0.08 * e
            turn = turn_base + 10.0 * np.sin(t_norm * np.pi * 2.0) + 5.0 * (b - 0.5)
            pitch = pitch_base + 7.0 * (c - 0.5)
            lateral = np.sin(t_norm * np.pi * 4.0 + control_number * 0.22) * lateral_base
            core_scale = 0.12 + 0.18 * e
            motif_rule = motif_cycle[control_number % len(motif_cycle)]
            motif_scale = 0.12 + 0.2 * e + 0.1 * o
            motif_x = 0.11 + 0.1 * c
            motif_y = lateral
            motif_z = 0.04 + 0.14 * o + 0.03 * b
            motif_rz = turn * 0.7
            motif_ry = 10.0 + pitch * 0.9
            echo_scale = 0.05 + 0.05 * b
            echo_x = -0.08 - 0.05 * e
            echo_y = -lateral * 0.55
            echo_rz = -turn * 0.22
            echo_ry = -pitch * 0.24

            lines.extend(
                [
                    f"rule {current_rule} {{",
                    f"  {{ s {_safe_float(core_scale)} }} sphere",
                    f"  {{ x {_safe_float(step)} y {_safe_float(lateral * 0.1)} rz {_safe_float(turn)} ry {_safe_float(pitch)} s {_safe_float(body_decay)} }} {next_rule}",
                    f"  {{ x {_safe_float(motif_x)} y {_safe_float(motif_y)} z {_safe_float(motif_z)} rz {_safe_float(motif_rz)} ry {_safe_float(motif_ry)} s {_safe_float(motif_scale)} }} {motif_rule}",
                    f"  {{ x {_safe_float(echo_x)} y {_safe_float(echo_y)} rz {_safe_float(echo_rz)} ry {_safe_float(echo_ry)} s {_safe_float(echo_scale)} }} echo",
                ]
            )

            if idx in peak_set:
                pulse_scale = 0.14 + 0.22 * e + 0.18 * o
                pulse_x = motif_x * 0.92
                pulse_z = motif_z + 0.12
                pulse_rz = motif_rz + 10.0
                pulse_ry = motif_ry + 8.0
                lines.append(
                    f"  {{ x {_safe_float(pulse_x)} y {_safe_float(motif_y)} z {_safe_float(pulse_z)} rz {_safe_float(pulse_rz)} ry {_safe_float(pulse_ry)} s {_safe_float(pulse_scale)} }} chronoPulse"
                )

            lines.extend(
                [
                    "}",
                    "",
                ]
            )

        lines.extend(
            [
                f"rule chronodTail maxdepth {max(8, int(maxdepth * 0.55))} {{",
                f"  {{ s {_safe_float(0.1 + 0.08 * energy)} }} sphere",
                f"  {{ x {_safe_float(spine_step * 0.94)} rz {_safe_float(turn_base * 0.78)} ry {_safe_float(pitch_base * 0.88)} s {_safe_float(body_decay * 0.985)} }} chronodTail",
                "}",
                "",
                "rule ribbonFin maxdepth 5 {",
                f"  {{ s {_safe_float(0.16 + 0.16 * brightness)} }} box",
                f"  {{ x {_safe_float(0.16 + 0.08 * brightness)} rz {_safe_float(18 + turn_base * 0.16)} ry {_safe_float(16 + pitch_base * 0.18)} s {_safe_float(0.82)} }} ribbonFin",
                "}",
                "",
                "rule vesselBud maxdepth 5 {",
                f"  {{ s {_safe_float(0.22 + 0.24 * energy)} }} sphere",
                f"  {{ x {_safe_float(0.15 + 0.08 * energy)} rz {_safe_float(-14 - turn_base * 0.08)} ry {_safe_float(10 + pitch_base * 0.14)} s {_safe_float(0.84)} }} vesselBud",
                "}",
                "",
                "rule helixHook maxdepth 6 {",
                f"  {{ s {_safe_float(0.14 + 0.14 * roughness)} }} cylinder",
                f"  {{ x {_safe_float(0.15 + 0.08 * roughness)} rz {_safe_float(24 + turn_base * 0.22)} ry {_safe_float(14 + pitch_base * 0.2)} s {_safe_float(0.82)} }} helixHook",
                f"  {{ x {_safe_float(0.12)} rz {_safe_float(-18 - turn_base * 0.1)} s {_safe_float(0.16 + 0.08 * brightness)} }} spark",
                "}",
                "",
                "rule terrainRidge maxdepth 5 {",
                f"  {{ s {_safe_float(0.14 + 0.12 * roughness)} }} box",
                f"  {{ x {_safe_float(0.14 + 0.06 * roughness)} rz {_safe_float(8 + turn_base * 0.08)} ry {_safe_float(8 + pitch_base * 0.12)} s {_safe_float(0.8)} }} terrainRidge",
                "}",
                "",
                "rule chronoPulse maxdepth 6 {",
                f"  {{ s {_safe_float(0.22 + 0.26 * energy)} }} sphere",
                f"  {{ x {_safe_float(0.15 + 0.08 * energy)} rz {_safe_float(20 + turn_base * 0.14)} ry {_safe_float(14 + pitch_base * 0.16)} s {_safe_float(0.82)} }} chronoPulse",
                f"  {{ x {_safe_float(0.12)} rz {_safe_float(-20 - turn_base * 0.08)} s {_safe_float(0.16 + 0.08 * roughness)} }} spark",
                "}",
                "",
                "rule echo maxdepth 4 {",
                f"  {{ s {_safe_float(0.06 + 0.05 * roughness)} }} sphere",
                f"  {{ x {_safe_float(0.1 + 0.04 * brightness)} rz {_safe_float(-10 - turn_base * 0.05)} ry {_safe_float(-8 - pitch_base * 0.08)} s {_safe_float(0.78)} }} echo",
                "}",
                "",
                "rule spark maxdepth 2 {",
                f"  {{ s {_safe_float(max(0.05, 0.07 + 0.06 * energy))} }} sphere",
                "}",
                "",
            ]
        )

        metadata = {
            "template": template,
            "seed": rng_seed,
            "max_events": int(max_events),
            "event_count_written": int(len(peaks)),
            "summary": {k: v for k, v in summary.items() if k != "peak_indices"},
            "grammar_parameters": {
                "maxdepth": maxdepth,
                "maxobjects": maxobjects,
                "body_scale": body_scale,
                "body_decay": body_decay,
                "spine_step": spine_step,
                "turn_base": turn_base,
                "pitch_base": pitch_base,
                "control_point_count": len(control_points),
            },
        }
        return "\n".join(lines), metadata

    if template == "chrono-body":
        maxdepth = int(20 + 10 * energy + 14 * density)
        maxobjects = int(1400 + 2800 * density + 2200 * roughness)
        body_scale = 0.66 + 0.8 * energy
        body_decay = 0.92 - 0.04 * roughness
        spine_step = 0.3 + 0.2 * energy
        turn_base = 12.0 + 34.0 * roughness
        pitch_base = 6.0 + 18.0 * brightness
        lateral_base = 0.1 + 0.28 * brightness
        control_points = _control_indices(len(features.times), peaks, minimum=14, maximum=24)
        peak_set = set(peaks)

        lines: list[str] = []
        lines.extend(
            [
                "/*",
                "  Generated by dsp-form-lab.",
                "  StructureSynth lane: chrono-body template.",
                "  A chronological body with motif references to ribbon, vessel, helix, and terrain lanes.",
                "*/",
                f"set seed {rng_seed}",
                f"set maxdepth {maxdepth}",
                f"set maxobjects {maxobjects}",
                "set background white",
                "start",
                "",
                "rule start {",
                f"  {{ s {_safe_float(body_scale)} }} chrono0",
                "}",
                "",
            ]
        )

        duration = max(features.duration_seconds, 1e-6)
        chrono_rule_names = [f"chrono{i}" for i in range(len(control_points))] or ["chrono0"]
        motif_cycle = ("ribbonFin", "vesselBud", "helixHook", "terrainRidge")

        for control_number, idx in enumerate(control_points):
            e = float(rms[idx]) if idx < len(rms) else energy
            c = float(centroid[idx]) if idx < len(centroid) else brightness
            b = float(bandwidth[idx]) if idx < len(bandwidth) else roughness
            o = float(onset[idx]) if idx < len(onset) else 0.0
            t_norm = float(features.times[idx] / duration) if idx < len(features.times) else 0.0

            current_rule = chrono_rule_names[control_number]
            next_rule = chrono_rule_names[control_number + 1] if control_number + 1 < len(chrono_rule_names) else "chronoTail"

            step = spine_step + 0.14 * e
            turn = turn_base + 16.0 * np.sin(t_norm * np.pi * 2.0) + 8.0 * (b - 0.5)
            pitch = pitch_base + 12.0 * (c - 0.5)
            lateral = np.sin(t_norm * np.pi * 3.0 + control_number * 0.35) * lateral_base
            core_scale = 0.14 + 0.16 * e
            motif_rule = motif_cycle[control_number % len(motif_cycle)]
            motif_scale = 0.11 + 0.16 * e + 0.08 * o
            motif_x = 0.2 + 0.18 * c
            motif_y = lateral
            motif_z = 0.08 + 0.22 * o + 0.05 * b
            motif_rz = turn * 0.62
            motif_ry = 12.0 + pitch * 0.8
            echo_scale = 0.07 + 0.08 * b
            echo_x = -0.12 - 0.08 * e
            echo_y = -lateral * 0.66
            echo_rz = -turn * 0.28
            echo_ry = -pitch * 0.32

            lines.extend(
                [
                    f"rule {current_rule} {{",
                    f"  {{ s {_safe_float(core_scale)} }} sphere",
                    f"  {{ x {_safe_float(step)} y {_safe_float(lateral * 0.16)} rz {_safe_float(turn)} ry {_safe_float(pitch)} s {_safe_float(body_decay)} }} {next_rule}",
                    f"  {{ x {_safe_float(motif_x)} y {_safe_float(motif_y)} z {_safe_float(motif_z)} rz {_safe_float(motif_rz)} ry {_safe_float(motif_ry)} s {_safe_float(motif_scale)} }} {motif_rule}",
                    f"  {{ x {_safe_float(echo_x)} y {_safe_float(echo_y)} rz {_safe_float(echo_rz)} ry {_safe_float(echo_ry)} s {_safe_float(echo_scale)} }} echo",
                ]
            )

            if idx in peak_set:
                pulse_scale = 0.16 + 0.24 * e + 0.18 * o
                pulse_x = motif_x * 0.86
                pulse_z = motif_z + 0.18
                pulse_rz = motif_rz + 14.0
                pulse_ry = motif_ry + 10.0
                lines.append(
                    f"  {{ x {_safe_float(pulse_x)} y {_safe_float(motif_y)} z {_safe_float(pulse_z)} rz {_safe_float(pulse_rz)} ry {_safe_float(pulse_ry)} s {_safe_float(pulse_scale)} }} chronoPulse"
                )

            lines.extend(
                [
                    "}",
                    "",
                ]
            )

        lines.extend(
            [
                f"rule chronoTail maxdepth {max(7, int(maxdepth * 0.5))} {{",
                f"  {{ s {_safe_float(0.12 + 0.08 * energy)} }} sphere",
                f"  {{ x {_safe_float(spine_step * 0.96)} rz {_safe_float(turn_base * 0.82)} ry {_safe_float(pitch_base * 0.9)} s {_safe_float(body_decay * 0.98)} }} chronoTail",
                "}",
                "",
                "rule ribbonFin maxdepth 4 {",
                f"  {{ s {_safe_float(0.12 + 0.14 * brightness)} }} box",
                f"  {{ x {_safe_float(0.18 + 0.12 * brightness)} rz {_safe_float(20 + turn_base * 0.18)} ry {_safe_float(18 + pitch_base * 0.22)} s {_safe_float(0.8)} }} ribbonFin",
                "}",
                "",
                "rule vesselBud maxdepth 4 {",
                f"  {{ s {_safe_float(0.18 + 0.22 * energy)} }} sphere",
                f"  {{ x {_safe_float(0.16 + 0.1 * energy)} rz {_safe_float(-16 - turn_base * 0.1)} ry {_safe_float(10 + pitch_base * 0.18)} s {_safe_float(0.82)} }} vesselBud",
                "}",
                "",
                "rule helixHook maxdepth 5 {",
                f"  {{ s {_safe_float(0.1 + 0.14 * roughness)} }} cylinder",
                f"  {{ x {_safe_float(0.16 + 0.1 * roughness)} rz {_safe_float(28 + turn_base * 0.24)} ry {_safe_float(16 + pitch_base * 0.26)} s {_safe_float(0.8)} }} helixHook",
                f"  {{ x {_safe_float(0.14)} rz {_safe_float(-22 - turn_base * 0.12)} s {_safe_float(0.18 + 0.08 * brightness)} }} spark",
                "}",
                "",
                "rule terrainRidge maxdepth 4 {",
                f"  {{ s {_safe_float(0.1 + 0.12 * roughness)} }} box",
                f"  {{ x {_safe_float(0.14 + 0.08 * roughness)} rz {_safe_float(10 + turn_base * 0.1)} ry {_safe_float(8 + pitch_base * 0.14)} s {_safe_float(0.78)} }} terrainRidge",
                "}",
                "",
                "rule chronoPulse maxdepth 5 {",
                f"  {{ s {_safe_float(0.18 + 0.24 * energy)} }} sphere",
                f"  {{ x {_safe_float(0.16 + 0.1 * energy)} rz {_safe_float(22 + turn_base * 0.16)} ry {_safe_float(16 + pitch_base * 0.18)} s {_safe_float(0.8)} }} chronoPulse",
                f"  {{ x {_safe_float(0.14)} rz {_safe_float(-24 - turn_base * 0.1)} s {_safe_float(0.18 + 0.08 * roughness)} }} spark",
                "}",
                "",
                "rule echo maxdepth 3 {",
                f"  {{ s {_safe_float(0.07 + 0.06 * roughness)} }} sphere",
                f"  {{ x {_safe_float(0.12 + 0.06 * brightness)} rz {_safe_float(-12 - turn_base * 0.06)} ry {_safe_float(-8 - pitch_base * 0.1)} s {_safe_float(0.76)} }} echo",
                "}",
                "",
                "rule spark maxdepth 2 {",
                f"  {{ s {_safe_float(max(0.05, 0.08 + 0.08 * energy))} }} sphere",
                "}",
                "",
            ]
        )

        metadata = {
            "template": template,
            "seed": rng_seed,
            "max_events": int(max_events),
            "event_count_written": int(len(peaks)),
            "summary": {k: v for k, v in summary.items() if k != "peak_indices"},
            "grammar_parameters": {
                "maxdepth": maxdepth,
                "maxobjects": maxobjects,
                "body_scale": body_scale,
                "body_decay": body_decay,
                "spine_step": spine_step,
                "turn_base": turn_base,
                "pitch_base": pitch_base,
                "control_point_count": len(control_points),
            },
        }
        return "\n".join(lines), metadata

    if template == "helix-vine":
        maxdepth = int(18 + 10 * energy + 12 * density)
        maxobjects = int(1200 + 2600 * density + 2200 * roughness)
        vine_scale = 0.64 + 0.82 * energy
        vine_decay = 0.91 - 0.04 * roughness
        spine_step = 0.28 + 0.18 * energy
        turn_base = 18.0 + 54.0 * roughness
        pitch_base = 8.0 + 22.0 * brightness
        rib_radius = 0.18 + 0.38 * brightness
        spark_scale = 0.08 + 0.1 * energy
        control_points = _control_indices(len(features.times), peaks, minimum=10, maximum=16)
        peak_set = set(peaks)

        lines: list[str] = []
        lines.extend(
            [
                "/*",
                "  Generated by dsp-form-lab.",
                "  StructureSynth lane: helix-vine template.",
                "  A continuous spiral spine carries smaller event ribs and buds.",
                "*/",
                f"set seed {rng_seed}",
                f"set maxdepth {maxdepth}",
                f"set maxobjects {maxobjects}",
                "set background white",
                "start",
                "",
                "rule start {",
                f"  {{ s {_safe_float(vine_scale)} }} vine0",
                "}",
                "",
            ]
        )

        duration = max(features.duration_seconds, 1e-6)
        vine_rule_names = [f"vine{i}" for i in range(len(control_points))] or ["vine0"]

        for control_number, idx in enumerate(control_points):
            e = float(rms[idx]) if idx < len(rms) else energy
            c = float(centroid[idx]) if idx < len(centroid) else brightness
            b = float(bandwidth[idx]) if idx < len(bandwidth) else roughness
            o = float(onset[idx]) if idx < len(onset) else 0.0
            t_norm = float(features.times[idx] / duration) if idx < len(features.times) else 0.0

            current_rule = vine_rule_names[control_number]
            next_rule = vine_rule_names[control_number + 1] if control_number + 1 < len(vine_rule_names) else "vineTail"

            step = spine_step + 0.12 * e
            turn = turn_base + 18.0 * np.sin(t_norm * np.pi * 2.0) + 12.0 * (c - 0.5)
            pitch = pitch_base + 10.0 * (c - 0.5) - 8.0 * (b - 0.5)
            core_scale = 0.16 + 0.14 * e
            rib_scale = 0.12 + 0.18 * o + 0.06 * b
            rib_x = rib_radius + 0.16 * c
            rib_y = np.sin(t_norm * np.pi * 4.0 + control_number * 0.4) * (0.08 + 0.18 * b)
            rib_z = 0.12 + 0.26 * o
            rib_rz = turn * 0.52
            rib_ry = 10.0 + pitch * 0.6
            spur_scale = 0.08 + 0.12 * b
            spur_x = -0.14 - 0.1 * e
            spur_y = -rib_y * 0.72
            spur_rz = -turn * 0.36
            spur_ry = -pitch * 0.48

            if c < 0.34:
                bud_rule = "vineBudLow"
            elif c < 0.68:
                bud_rule = "vineBudMid"
            else:
                bud_rule = "vineBudHigh"

            attachment_rule = bud_rule
            attachment_scale = rib_scale
            attachment_z = rib_z
            attachment_rz = rib_rz
            attachment_ry = rib_ry
            if idx in peak_set:
                attachment_rule = "vinePulse"
                attachment_scale = 0.18 + 0.28 * e + 0.18 * o
                attachment_z = rib_z + 0.16
                attachment_rz = rib_rz + 12.0
                attachment_ry = rib_ry + 8.0

            lines.extend(
                [
                    f"rule {current_rule} {{",
                    f"  {{ s {_safe_float(core_scale)} }} sphere",
                    f"  {{ x {_safe_float(step)} rz {_safe_float(turn)} ry {_safe_float(pitch)} s {_safe_float(vine_decay)} }} {next_rule}",
                    f"  {{ x {_safe_float(rib_x)} y {_safe_float(rib_y)} z {_safe_float(attachment_z)} rz {_safe_float(attachment_rz)} ry {_safe_float(attachment_ry)} s {_safe_float(attachment_scale)} }} {attachment_rule}",
                    f"  {{ x {_safe_float(spur_x)} y {_safe_float(spur_y)} rz {_safe_float(spur_rz)} ry {_safe_float(spur_ry)} s {_safe_float(spur_scale)} }} vineSpur",
                    "}",
                    "",
                ]
            )

        lines.extend(
            [
                f"rule vineTail maxdepth {max(6, int(maxdepth * 0.55))} {{",
                f"  {{ s {_safe_float(0.12 + 0.08 * energy)} }} sphere",
                f"  {{ x {_safe_float(spine_step * 0.94)} rz {_safe_float(turn_base * 0.92)} ry {_safe_float(pitch_base * 0.84)} s {_safe_float(vine_decay * 0.98)} }} vineTail",
                "}",
                "",
                "rule vineBudLow maxdepth 4 {",
                f"  {{ s {_safe_float(0.18 + 0.28 * energy)} }} sphere",
                f"  {{ x {_safe_float(0.22 + 0.12 * energy)} rz {_safe_float(-18 - turn_base * 0.1)} ry {_safe_float(10 + pitch_base * 0.18)} s {_safe_float(0.82)} }} vineBudLow",
                "}",
                "",
                "rule vineBudMid maxdepth 5 {",
                f"  {{ s {_safe_float(0.14 + 0.18 * roughness)} }} box",
                f"  {{ x {_safe_float(0.2 + 0.12 * roughness)} rz {_safe_float(18 + turn_base * 0.14)} ry {_safe_float(14 + pitch_base * 0.22)} s {_safe_float(0.8)} }} vineBudMid",
                f"  {{ x {_safe_float(0.18)} rz {_safe_float(-20 - turn_base * 0.08)} s {_safe_float(0.24 + 0.1 * energy)} }} spark",
                "}",
                "",
                "rule vineBudHigh maxdepth 4 {",
                f"  {{ s {_safe_float(0.1 + 0.16 * brightness)} }} sphere",
                f"  {{ x {_safe_float(0.18 + 0.12 * brightness)} rz {_safe_float(26 + turn_base * 0.18)} ry {_safe_float(18 + pitch_base * 0.26)} s {_safe_float(0.74)} }} vineBudHigh",
                f"  {{ x {_safe_float(0.16)} rz {_safe_float(-30 - turn_base * 0.1)} s {_safe_float(0.18 + 0.1 * roughness)} }} spark",
                "}",
                "",
                "rule vinePulse maxdepth 5 {",
                f"  {{ s {_safe_float(0.2 + 0.3 * energy)} }} sphere",
                f"  {{ x {_safe_float(0.18 + 0.14 * energy)} rz {_safe_float(22 + turn_base * 0.16)} ry {_safe_float(16 + pitch_base * 0.2)} s {_safe_float(0.8)} }} vinePulse",
                f"  {{ x {_safe_float(0.16)} rz {_safe_float(-24 - turn_base * 0.1)} s {_safe_float(0.2 + 0.12 * roughness)} }} spark",
                "}",
                "",
                "rule vineSpur maxdepth 3 {",
                f"  {{ s {_safe_float(0.09 + 0.08 * roughness)} }} sphere",
                f"  {{ x {_safe_float(0.14 + 0.08 * brightness)} rz {_safe_float(-14 - turn_base * 0.06)} ry {_safe_float(-10 - pitch_base * 0.14)} s {_safe_float(0.76)} }} vineSpur",
                "}",
                "",
                "rule spark maxdepth 2 {",
                f"  {{ s {_safe_float(max(0.05, spark_scale))} }} sphere",
                "}",
                "",
            ]
        )

        metadata = {
            "template": template,
            "seed": rng_seed,
            "max_events": int(max_events),
            "event_count_written": int(len(peaks)),
            "summary": {k: v for k, v in summary.items() if k != "peak_indices"},
            "grammar_parameters": {
                "maxdepth": maxdepth,
                "maxobjects": maxobjects,
                "vine_scale": vine_scale,
                "vine_decay": vine_decay,
                "spine_step": spine_step,
                "turn_base": turn_base,
                "pitch_base": pitch_base,
                "rib_radius": rib_radius,
                "control_point_count": len(control_points),
            },
        }
        return "\n".join(lines), metadata

    if template == "helix-thread":
        maxdepth = int(14 + 10 * energy + 10 * density)
        maxobjects = int(700 + 2200 * density + 1800 * roughness)
        thread_scale = 0.58 + 0.75 * energy
        thread_decay = 0.89 - 0.04 * roughness
        step_base = 0.38 + 0.24 * energy
        turn_base = 14.0 + 56.0 * roughness
        pitch_base = 10.0 + 24.0 * brightness
        node_orbit = 0.18 + 0.6 * brightness
        tail_scale = 0.16 + 0.12 * energy

        lines: list[str] = []
        lines.extend(
            [
                "/*",
                "  Generated by dsp-form-lab.",
                "  StructureSynth lane: helix-thread template.",
                "  Event moments are threaded along one recursive path instead of spawned as separate islands.",
                "*/",
                f"set seed {rng_seed}",
                f"set maxdepth {maxdepth}",
                f"set maxobjects {maxobjects}",
                "set background white",
                "start",
                "",
                "rule start {",
                f"  {{ s {_safe_float(thread_scale)} }} thread0",
                "}",
                "",
            ]
        )

        duration = max(features.duration_seconds, 1e-6)
        thread_rule_names = [f"thread{i}" for i in range(len(peaks))] or ["thread0"]
        for event_number, idx in enumerate(peaks):
            e = float(rms[idx]) if idx < len(rms) else energy
            c = float(centroid[idx]) if idx < len(centroid) else brightness
            b = float(bandwidth[idx]) if idx < len(bandwidth) else roughness
            o = float(onset[idx]) if idx < len(onset) else 0.0
            t_norm = float(features.times[idx] / duration) if idx < len(features.times) else 0.0

            step = step_base + 0.18 * e
            turn = turn_base * (0.55 + b * 0.75)
            pitch = pitch_base * (0.65 + c * 0.45)
            scale = 0.12 + 0.26 * e
            node_x = 0.18 + 0.22 * c
            node_y = np.cos(t_norm * np.pi * 2.0 + event_number * 0.33) * node_orbit
            node_z = 0.1 + 0.42 * o
            node_rz = 10.0 + 40.0 * b
            node_ry = -10.0 + 28.0 * c
            node_scale = 0.16 + 0.34 * e + 0.2 * o

            if c < 0.34:
                node_rule = "threadLow"
            elif c < 0.68:
                node_rule = "threadMid"
            else:
                node_rule = "threadHigh"

            current_rule = thread_rule_names[event_number]
            next_rule = thread_rule_names[event_number + 1] if event_number + 1 < len(thread_rule_names) else "tail"
            lines.extend(
                [
                    f"rule {current_rule} {{",
                    f"  {{ s {_safe_float(scale)} }} sphere",
                    f"  {{ x {_safe_float(step)} rz {_safe_float(turn)} ry {_safe_float(pitch)} s {_safe_float(thread_decay)} }} {next_rule}",
                    f"  {{ x {_safe_float(node_x)} y {_safe_float(node_y)} z {_safe_float(node_z)} rz {_safe_float(node_rz)} ry {_safe_float(node_ry)} s {_safe_float(node_scale)} }} {node_rule}",
                    "}",
                    "",
                ]
            )

        lines.extend(
            [
                f"rule tail maxdepth {max(5, int(maxdepth * 0.5))} {{",
                f"  {{ s {_safe_float(tail_scale)} }} sphere",
                f"  {{ x {_safe_float(step_base * 0.92)} rz {_safe_float(turn_base * 0.88)} ry {_safe_float(pitch_base * 0.82)} s {_safe_float(thread_decay * 0.98)} }} tail",
                "}",
                "",
                "rule threadLow maxdepth 5 {",
                f"  {{ s {_safe_float(0.28 + 0.38 * energy)} }} sphere",
                f"  {{ x {_safe_float(0.34 + 0.18 * energy)} rz {_safe_float(-18 - turn_base * 0.12)} ry {_safe_float(8 + pitch_base * 0.22)} s {_safe_float(0.82)} }} threadLow",
                "}",
                "",
                "rule threadMid maxdepth 6 {",
                f"  {{ s {_safe_float(0.18 + 0.24 * roughness)} }} box",
                f"  {{ x {_safe_float(0.28 + 0.16 * roughness)} rz {_safe_float(16 + turn_base * 0.16)} ry {_safe_float(14 + pitch_base * 0.24)} s {_safe_float(0.8)} }} threadMid",
                f"  {{ x {_safe_float(0.24)} rz {_safe_float(-24 - turn_base * 0.1)} s {_safe_float(0.44 + 0.12 * energy)} }} spark",
                "}",
                "",
                "rule threadHigh maxdepth 4 {",
                f"  {{ s {_safe_float(0.12 + 0.2 * brightness)} }} sphere",
                f"  {{ x {_safe_float(0.22 + 0.16 * brightness)} rz {_safe_float(28 + turn_base * 0.2)} ry {_safe_float(18 + pitch_base * 0.28)} s {_safe_float(0.72)} }} threadHigh",
                f"  {{ x {_safe_float(0.18)} rz {_safe_float(-36 - turn_base * 0.12)} s {_safe_float(0.28 + 0.14 * roughness)} }} spark",
                "}",
                "",
                "rule spark maxdepth 2 {",
                f"  {{ s {_safe_float(max(0.06, tail_scale * 0.5))} }} sphere",
                "}",
                "",
            ]
        )

        metadata = {
            "template": template,
            "seed": rng_seed,
            "max_events": int(max_events),
            "event_count_written": int(len(peaks)),
            "summary": {k: v for k, v in summary.items() if k != "peak_indices"},
            "grammar_parameters": {
                "maxdepth": maxdepth,
                "maxobjects": maxobjects,
                "thread_scale": thread_scale,
                "thread_decay": thread_decay,
                "step_base": step_base,
                "turn_base": turn_base,
                "pitch_base": pitch_base,
                "node_orbit": node_orbit,
                "tail_scale": tail_scale,
            },
        }
        return "\n".join(lines), metadata

    if template == "helix-coil":
        maxdepth = int(16 + 12 * energy + 12 * density)
        maxobjects = int(800 + 3200 * density + 2200 * roughness)
        coil_scale = 0.52 + 0.9 * energy
        coil_step = 0.46 + 0.38 * energy
        coil_turn = 18.0 + 86.0 * roughness
        coil_pitch = 10.0 + 32.0 * brightness
        coil_decay = 0.93 - 0.05 * roughness
        node_scale = 0.2 + 0.42 * max(0.08, energy)
        orbit_radius = 2.4 + 7.6 * brightness

        lines: list[str] = []
        lines.extend(
            [
                "/*",
                "  Generated by dsp-form-lab.",
                "  StructureSynth lane: helix-coil template.",
                "  Time climbs a recursive spiral; onset events become attached nodes.",
                "*/",
                f"set seed {rng_seed}",
                f"set maxdepth {maxdepth}",
                f"set maxobjects {maxobjects}",
                "set background white",
                "start",
                "",
                "rule start {",
                f"  {{ s {_safe_float(coil_scale)} }} coil",
            ]
        )

        duration = max(features.duration_seconds, 1e-6)
        for event_number, idx in enumerate(peaks):
            t_norm = float(features.times[idx] / duration) if idx < len(features.times) else 0.0
            e = float(rms[idx]) if idx < len(rms) else energy
            c = float(centroid[idx]) if idx < len(centroid) else brightness
            b = float(bandwidth[idx]) if idx < len(bandwidth) else roughness
            o = float(onset[idx]) if idx < len(onset) else 0.0

            phase = (t_norm * np.pi * 2.0 * (2.0 + density * 3.0)) + event_number * 0.18
            x = np.cos(phase) * orbit_radius
            y = np.sin(phase) * orbit_radius
            z = 0.4 + t_norm * (5.2 + 2.4 * energy) + 1.4 * e
            scale = 0.24 + 0.72 * e + 0.42 * o
            rz = np.degrees(phase) + coil_turn * 0.2
            ry = -16.0 + 32.0 * c + 10.0 * (b - 0.5)

            if c < 0.34:
                rule_name = "nodeLow"
            elif c < 0.68:
                rule_name = "nodeMid"
            else:
                rule_name = "nodeHigh"

            lines.append(
                "  "
                + f"{{ x {_safe_float(x)} y {_safe_float(y)} z {_safe_float(z)} "
                + f"rz {_safe_float(rz)} ry {_safe_float(ry)} s {_safe_float(scale)} }} {rule_name}"
            )

        lines.extend(
            [
                "}",
                "",
                f"rule coil maxdepth {max(6, int(maxdepth * 0.55))} {{",
                f"  {{ s {_safe_float(0.18 + 0.2 * energy)} }} sphere",
                f"  {{ x {_safe_float(coil_step)} rz {_safe_float(coil_turn)} ry {_safe_float(coil_pitch)} s {_safe_float(coil_decay)} }} coil",
                f"  {{ x {_safe_float(coil_step * 0.78)} rz {_safe_float(-coil_turn * 0.42)} ry {_safe_float(coil_pitch * 0.68)} s {_safe_float(0.74 + 0.12 * energy)} }} turn",
                "}",
                "",
                f"rule turn maxdepth {max(4, int(4 + density * 7))} {{",
                f"  {{ s {_safe_float(0.12 + 0.18 * roughness)} }} cylinder",
                f"  {{ x {_safe_float(0.42 + 0.22 * energy)} rz {_safe_float(coil_turn * 0.58)} ry {_safe_float(coil_pitch * 0.52)} s {_safe_float(0.8 + 0.08 * (1.0 - roughness))} }} turn",
                f"  {{ x {_safe_float(0.34 + 0.18 * brightness)} rz {_safe_float(-coil_turn * 0.32)} s {_safe_float(0.6 + 0.14 * energy)} }} spark",
                "}",
                "",
                "rule nodeLow maxdepth 6 {",
                f"  {{ s {_safe_float(0.36 + 0.46 * energy)} }} sphere",
                f"  {{ x {_safe_float(0.48 + 0.24 * energy)} rz {_safe_float(-22 - coil_turn * 0.12)} ry {_safe_float(8 + coil_pitch * 0.25)} s {_safe_float(0.8)} }} nodeLow",
                "}",
                "",
                "rule nodeMid maxdepth 7 {",
                f"  {{ s {_safe_float(0.24 + 0.28 * roughness)} }} box",
                f"  {{ x {_safe_float(0.42 + 0.18 * roughness)} rz {_safe_float(18 + coil_turn * 0.15)} ry {_safe_float(14 + coil_pitch * 0.3)} s {_safe_float(0.78)} }} nodeMid",
                f"  {{ x {_safe_float(0.32)} rz {_safe_float(-26 - coil_turn * 0.1)} s {_safe_float(0.52 + 0.16 * energy)} }} spark",
                "}",
                "",
                "rule nodeHigh maxdepth 5 {",
                f"  {{ s {_safe_float(0.14 + 0.26 * brightness)} }} sphere",
                f"  {{ x {_safe_float(0.34 + 0.22 * brightness)} rz {_safe_float(32 + coil_turn * 0.22)} ry {_safe_float(18 + coil_pitch * 0.36)} s {_safe_float(0.72)} }} nodeHigh",
                f"  {{ x {_safe_float(0.24)} rz {_safe_float(-40 - coil_turn * 0.14)} s {_safe_float(0.34 + 0.18 * roughness)} }} spark",
                "}",
                "",
                "rule spark maxdepth 2 {",
                f"  {{ s {_safe_float(max(0.08, node_scale * 0.55))} }} sphere",
                "}",
                "",
            ]
        )

        metadata = {
            "template": template,
            "seed": rng_seed,
            "max_events": int(max_events),
            "event_count_written": int(len(peaks)),
            "summary": {k: v for k, v in summary.items() if k != "peak_indices"},
            "grammar_parameters": {
                "maxdepth": maxdepth,
                "maxobjects": maxobjects,
                "coil_scale": coil_scale,
                "coil_step": coil_step,
                "coil_turn": coil_turn,
                "coil_pitch": coil_pitch,
                "coil_decay": coil_decay,
                "node_scale": node_scale,
                "orbit_radius": orbit_radius,
            },
        }
        return "\n".join(lines), metadata

    if template == "radial-burst":
        maxdepth = int(14 + 12 * energy + 14 * density)
        maxobjects = int(700 + 2800 * density + 2400 * brightness)
        ring_radius = 4.0 + 12.0 * brightness
        core_scale = 0.35 + 0.9 * energy
        burst_step = 0.55 + 0.45 * roughness
        spiral = 12.0 + 110.0 * roughness
        detail_scale = 0.12 + 0.28 * max(0.05, brightness)

        lines: list[str] = []
        lines.extend(
            [
                "/*",
                "  Generated by dsp-form-lab.",
                "  StructureSynth lane: radial-burst template.",
                "*/",
                f"set seed {rng_seed}",
                f"set maxdepth {maxdepth}",
                f"set maxobjects {maxobjects}",
                "set background white",
                "start",
                "",
                "rule start {",
                f"  {{ s {_safe_float(core_scale)} }} core",
                f"  {{ s {_safe_float(0.8 + 0.6 * density)} }} ring",
            ]
        )

        duration = max(features.duration_seconds, 1e-6)
        for event_number, idx in enumerate(peaks):
            t_norm = float(features.times[idx] / duration) if idx < len(features.times) else 0.0
            e = float(rms[idx]) if idx < len(rms) else energy
            c = float(centroid[idx]) if idx < len(centroid) else brightness
            o = float(onset[idx]) if idx < len(onset) else 0.0
            phase = t_norm * np.pi * 2.0 + event_number * 0.22
            x = np.cos(phase) * ring_radius
            y = np.sin(phase) * ring_radius
            z = 0.45 + e * 1.8 + o * 0.65
            scale = 0.25 + 1.0 * e + 0.4 * o
            rz = np.degrees(phase) + spiral * 0.1
            ry = -14.0 + 28.0 * c

            if c < 0.34:
                rule_name = "burstLow"
            elif c < 0.68:
                rule_name = "burstMid"
            else:
                rule_name = "burstHigh"

            lines.append(
                "  "
                + f"{{ x {_safe_float(x)} y {_safe_float(y)} z {_safe_float(z)} "
                + f"rz {_safe_float(rz)} ry {_safe_float(ry)} s {_safe_float(scale)} }} {rule_name}"
            )

        lines.extend(
            [
                "}",
                "",
                f"rule core maxdepth {max(5, int(maxdepth * 0.6))} {{",
                f"  {{ s {_safe_float(0.34 + 0.55 * energy)} }} sphere",
                f"  {{ x {_safe_float(0.42 + 0.35 * energy)} rz {_safe_float(spiral * 0.18)} ry {_safe_float(22 + brightness * 28)} s {_safe_float(0.8 + 0.09 * energy)} }} core",
                "}",
                "",
                f"rule ring maxdepth {max(4, int(4 + density * 7))} {{",
                f"  {{ s {_safe_float(0.2 + 0.32 * roughness)} }} box",
                f"  {{ x {_safe_float(burst_step)} rz {_safe_float(spiral * 0.32)} ry {_safe_float(30 + brightness * 25)} s {_safe_float(0.78 + 0.12 * (1.0 - roughness))} }} ring",
                f"  {{ x {_safe_float(0.38 + 0.16 * energy)} rz {_safe_float(-spiral * 0.25)} s {_safe_float(0.66)} }} spark",
                "}",
                "",
                "rule burstLow maxdepth 6 {",
                f"  {{ s {_safe_float(0.58 + 0.65 * energy)} }} sphere",
                f"  {{ x {_safe_float(0.64 + 0.28 * energy)} rz {_safe_float(-26 - spiral * 0.12)} ry {_safe_float(8 + 20 * brightness)} s {_safe_float(0.82)} }} burstLow",
                "}",
                "",
                "rule burstMid maxdepth 7 {",
                f"  {{ s {_safe_float(0.42 + 0.42 * roughness)} }} box",
                f"  {{ x {_safe_float(0.56 + 0.2 * roughness)} rz {_safe_float(18 + spiral * 0.16)} ry {_safe_float(16 + 24 * brightness)} s {_safe_float(0.78)} }} burstMid",
                f"  {{ x {_safe_float(0.4)} rz {_safe_float(-32 - spiral * 0.14)} s {_safe_float(0.58 + 0.16 * energy)} }} spark",
                "}",
                "",
                "rule burstHigh maxdepth 5 {",
                f"  {{ s {_safe_float(0.24 + 0.36 * brightness)} }} sphere",
                f"  {{ x {_safe_float(0.46 + 0.28 * brightness)} rz {_safe_float(36 + spiral * 0.24)} ry {_safe_float(20 + 30 * brightness)} s {_safe_float(0.72)} }} burstHigh",
                f"  {{ x {_safe_float(0.34)} rz {_safe_float(-44 - spiral * 0.2)} s {_safe_float(0.44 + 0.2 * roughness)} }} spark",
                "}",
                "",
                "rule spark maxdepth 2 {",
                f"  {{ s {_safe_float(max(0.08, detail_scale * 0.6))} }} sphere",
                "}",
                "",
            ]
        )

        metadata = {
            "template": template,
            "seed": rng_seed,
            "max_events": int(max_events),
            "event_count_written": int(len(peaks)),
            "summary": {k: v for k, v in summary.items() if k != "peak_indices"},
            "grammar_parameters": {
                "maxdepth": maxdepth,
                "maxobjects": maxobjects,
                "ring_radius": ring_radius,
                "core_scale": core_scale,
                "burst_step": burst_step,
                "spiral": spiral,
                "detail_scale": detail_scale,
            },
        }
        return "\n".join(lines), metadata

    lines: list[str] = []
    lines.extend(
        [
            "/*",
            "  Generated by dsp-form-lab.",
            "  StructureSynth lane: captured WAV -> audio features -> EisenScript grammar.",
            "  Treat this as a grammar score, not as the final printable mesh.",
            "*/",
            f"set seed {rng_seed}",
            f"set maxdepth {maxdepth}",
            f"set maxobjects {maxobjects}",
            "set background white",
            "start",
            "",
            "rule start {",
            f"  {{ s {_safe_float(trunk_scale)} }} trunk",
        ]
    )

    duration = max(features.duration_seconds, 1e-6)
    for event_number, idx in enumerate(peaks):
        t_norm = float(features.times[idx] / duration) if idx < len(features.times) else 0.0
        e = float(rms[idx]) if idx < len(rms) else energy
        c = float(centroid[idx]) if idx < len(centroid) else brightness
        b = float(bandwidth[idx]) if idx < len(bandwidth) else roughness
        o = float(onset[idx]) if idx < len(onset) else 0.0

        # Spread event calls in a shallow arc. The transforms remain simple so
        # they are easy to edit directly inside StructureSynth.
        x = -12.0 + 24.0 * t_norm
        y = (c - 0.5) * 8.0
        z = 0.7 + event_number * 0.18 + e * 1.3
        scale = 0.32 + 1.15 * e + 0.35 * o
        rz = -42.0 + 84.0 * t_norm + twist * 0.15
        ry = -18.0 + 36.0 * c

        if c < 0.34:
            rule_name = "eventLow"
        elif c < 0.68:
            rule_name = "eventMid"
        else:
            rule_name = "eventHigh"

        # Add one line per captured event. These lines are the clearest place to
        # hand-edit the sonic structure after generation. Rule names are
        # intentionally letter-only/camelCase for compatibility with older
        # StructureSynth/EisenScript parsers and browser ports.
        lines.append(
            "  "
            + f"{{ x {_safe_float(x)} y {_safe_float(y)} z {_safe_float(z)} "
            + f"rz {_safe_float(rz)} ry {_safe_float(ry)} s {_safe_float(scale)} }} {rule_name}"
        )

    lines.extend(
        [
            "}",
            "",
            f"rule trunk maxdepth {max(6, int(maxdepth * 0.45))} {{",
            f"  {{ s {_safe_float(0.42 + 0.5 * energy)} }} sphere",
            f"  {{ x {_safe_float(trunk_step)} rz {_safe_float(twist * 0.22)} ry {_safe_float(branch_angle * 0.28)} s {_safe_float(trunk_decay)} }} trunk",
            f"  {{ x {_safe_float(trunk_step * 0.72)} rz {_safe_float(-branch_angle)} ry {_safe_float(branch_angle * 0.7)} s {_safe_float(branch_decay)} }} branch",
            f"  {{ x {_safe_float(trunk_step * 0.64)} rz {_safe_float(branch_angle)} ry {_safe_float(-branch_angle * 0.55)} s {_safe_float(branch_decay * 0.94)} }} branch",
            "}",
            "",
            f"rule branch maxdepth {max(4, int(6 + density * 8))} {{",
            f"  {{ s {_safe_float(0.28 + 0.45 * roughness)} }} box",
            f"  {{ x {_safe_float(0.55 + 0.35 * energy)} rz {_safe_float(branch_angle)} ry {_safe_float(twist * 0.2)} s {_safe_float(branch_decay)} }} branch",
            f"  {{ x {_safe_float(0.46 + 0.25 * brightness)} rz {_safe_float(-branch_angle * 0.8)} ry {_safe_float(-twist * 0.16)} s {_safe_float(branch_decay * 0.9)} }} twig",
            "}",
            "",
            f"rule twig maxdepth {max(3, int(4 + density * 6))} {{",
            f"  {{ s {_safe_float(detail_scale)} }} sphere",
            f"  {{ x {_safe_float(0.38 + 0.22 * brightness)} rz {_safe_float(twist * 0.35)} ry {_safe_float(branch_angle * 0.45)} s {_safe_float(0.72 + 0.12 * energy)} }} twig",
            "}",
            "",
            "rule eventLow maxdepth 6 {",
            f"  {{ s {_safe_float(0.74 + energy)} }} sphere",
            f"  {{ x {_safe_float(0.78 + energy)} rz {_safe_float(-18 - twist * 0.18)} ry {_safe_float(8 + branch_angle * 0.2)} s {_safe_float(0.82)} }} eventLow",
            "}",
            "",
            "rule eventMid maxdepth 7 {",
            f"  {{ s {_safe_float(0.45 + roughness)} }} box",
            f"  {{ x {_safe_float(0.68 + roughness)} rz {_safe_float(branch_angle)} ry {_safe_float(12 + brightness * 25)} s {_safe_float(0.8)} }} eventMid",
            f"  {{ x {_safe_float(0.54)} rz {_safe_float(-branch_angle * 0.85)} s {_safe_float(0.62 + 0.18 * energy)} }} twig",
            "}",
            "",
            "rule eventHigh maxdepth 5 {",
            f"  {{ s {_safe_float(0.22 + brightness * 0.42)} }} sphere",
            f"  {{ x {_safe_float(0.46 + brightness * 0.34)} rz {_safe_float(34 + twist * 0.45)} ry {_safe_float(18 + branch_angle * 0.35)} s {_safe_float(0.72)} }} eventHigh",
            f"  {{ x {_safe_float(0.35)} rz {_safe_float(-52 - twist * 0.2)} s {_safe_float(0.48 + 0.22 * roughness)} }} sparkle",
            "}",
            "",
            "rule sparkle maxdepth 2 {",
            f"  {{ s {_safe_float(max(0.08, detail_scale * 0.55))} }} sphere",
            "}",
            "",
        ]
    )

    metadata = {
        "template": template,
        "seed": rng_seed,
        "max_events": int(max_events),
        "event_count_written": int(len(peaks)),
        "summary": {k: v for k, v in summary.items() if k != "peak_indices"},
        "grammar_parameters": {
            "maxdepth": maxdepth,
            "maxobjects": maxobjects,
            "trunk_scale": trunk_scale,
            "trunk_step": trunk_step,
            "trunk_decay": trunk_decay,
            "branch_angle": branch_angle,
            "twist": twist,
            "branch_decay": branch_decay,
            "detail_scale": detail_scale,
        },
    }
    return "\n".join(lines), metadata


def write_structuresynth_grammar(
    features: AudioFeatures,
    out_path: str | Path,
    *,
    seed: int = 0,
    template: str = "onset-lattice",
    max_events: int = 24,
    onset_threshold: float = 0.62,
) -> dict[str, Any]:
    """Write an EisenScript grammar and sidecar manifest."""
    path = ensure_parent(out_path)
    grammar, metadata = generate_eisenscript(
        features,
        seed=seed,
        template=template,
        max_events=max_events,
        onset_threshold=onset_threshold,
    )
    path.write_text(grammar, encoding="utf-8")

    manifest_path = path.with_suffix(".json")
    manifest: dict[str, Any] = {
        "created_utc": utc_now_iso(),
        "generator": f"structuresynth/{template}",
        "seed": stable_seed(seed),
        "parameters": {
            "template": template,
            "max_events": max_events,
            "onset_threshold": onset_threshold,
        },
        "seed_usage": "grammar_rng",
        "audio": features.to_manifest(),
        "structuresynth": metadata,
        "provenance": runtime_provenance(),
        "outputs": {
            "eisenscript": str(path),
            "manifest": str(manifest_path),
            "expected_next_step": "Open the .es file in StructureSynth or BrowserSynth, export OBJ, then inspect/repair like any other generated mesh.",
        },
    }
    write_json(manifest_path, manifest)
    return manifest
