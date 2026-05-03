from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import numpy as np
from scipy.io import wavfile

from .audio_features import load_audio_features, save_feature_csv
from .generators.helix import write_helix
from .generators.implicit_field import write_implicit_field
from .generators.ribbon import write_ribbon
from .generators.terrain import write_terrain
from .generators.vessel import write_vessel
from .render.contact_sheet import build_contact_sheet
from .structuresynth import write_structuresynth_grammar
from .utils import write_json


PARAM_SWEEP_SPECS: dict[str, dict[str, type[Any]]] = {
    "terrain": {
        "width": float,
        "depth": float,
        "height": float,
        "base": float,
        "texture_noise_mm": float,
    },
    "ribbon": {
        "length": float,
        "width": float,
        "thickness": float,
        "height": float,
        "lateral": float,
        "twist": float,
        "wobble_mm": float,
    },
    "vessel": {
        "height": float,
        "base_radius": float,
        "radial_amp": float,
        "layers": int,
        "ridge_amp": float,
        "angle_jitter_deg": float,
        "radius_noise_mm": float,
    },
    "helix": {
        "height": float,
        "base_radius": float,
        "radial_amp": float,
        "turns": float,
        "tube_radius": float,
        "ridge_amp": float,
        "angle_jitter_deg": float,
        "radius_noise_mm": float,
    },
    "field": {
        "resolution": int,
        "level": float,
        "scale": float,
    },
    "ssynth": {
        "template": str,
        "max_events": int,
        "onset_threshold": float,
    },
}


def _require_positive(parser: argparse.ArgumentParser, value: float | int, *, name: str) -> None:
    if value <= 0:
        parser.error(f"{name} must be > 0.")


def _require_non_negative(parser: argparse.ArgumentParser, value: float | int, *, name: str) -> None:
    if value < 0:
        parser.error(f"{name} must be >= 0.")


def _coerce_param_value(raw: str, caster: type[Any]) -> Any:
    text = raw.strip()
    if caster is int:
        return int(text)
    if caster is float:
        return float(text)
    return text


def _parse_param_sweep_values(generator: str, param: str, values: str) -> list[Any]:
    if generator not in PARAM_SWEEP_SPECS:
        raise ValueError(f"Unsupported generator: {generator}")
    if param not in PARAM_SWEEP_SPECS[generator]:
        raise ValueError(f"Parameter '{param}' is not sweepable for generator '{generator}'.")
    caster = PARAM_SWEEP_SPECS[generator][param]
    parsed = [_coerce_param_value(chunk, caster) for chunk in values.split(",") if chunk.strip()]
    if not parsed:
        raise ValueError("At least one parameter value is required.")
    return parsed


def _validate_param_sweep_spec(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    try:
        parsed = _parse_param_sweep_values(args.generator, args.param, args.values)
    except ValueError as exc:
        parser.error(str(exc))
    if len(parsed) < 2:
        parser.error("--values must contain at least two entries for a sweep.")
    if args.generator == "ssynth" and args.param == "template":
        allowed = {"onset-lattice", "radial-burst", "helix-coil", "helix-thread", "helix-vine", "chrono-body", "chrono-body-dense"}
        if any(value not in allowed for value in parsed):
            parser.error("--values for ssynth template must be onset-lattice, radial-burst, helix-coil, helix-thread, helix-vine, chrono-body, and/or chrono-body-dense.")


def _validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.command == "sample":
        _require_positive(parser, args.seconds, name="--seconds")
        _require_positive(parser, args.sr, name="--sr")
        return
    if args.command == "contact-sheet":
        _require_positive(parser, args.cols, name="--cols")
        _require_positive(parser, args.tile_width, name="--tile-width")
        _require_positive(parser, args.tile_height, name="--tile-height")
        return

    _require_positive(parser, args.sr, name="--sr")
    _require_positive(parser, args.hop, name="--hop")
    if args.command == "terrain":
        if args.width is not None:
            _require_positive(parser, args.width, name="--width")
        _require_positive(parser, args.depth, name="--depth")
        if args.height is not None:
            _require_positive(parser, args.height, name="--height")
        _require_non_negative(parser, args.base, name="--base")
        _require_non_negative(parser, args.texture_noise_mm, name="--texture-noise-mm")
    elif args.command == "ribbon":
        _require_positive(parser, args.length, name="--length")
        if args.width is not None:
            _require_positive(parser, args.width, name="--width")
        _require_positive(parser, args.thickness, name="--thickness")
        if args.height is not None:
            _require_positive(parser, args.height, name="--height")
        _require_non_negative(parser, args.lateral, name="--lateral")
        _require_non_negative(parser, args.wobble_mm, name="--wobble-mm")
    elif args.command == "vessel":
        if args.height is not None:
            _require_positive(parser, args.height, name="--height")
        _require_positive(parser, args.base_radius, name="--base-radius")
        _require_non_negative(parser, args.radial_amp, name="--radial-amp")
        _require_positive(parser, args.layers, name="--layers")
        if args.layers < 2:
            parser.error("--layers must be >= 2.")
        _require_non_negative(parser, args.ridge_amp, name="--ridge-amp")
        _require_non_negative(parser, args.angle_jitter_deg, name="--angle-jitter-deg")
        _require_non_negative(parser, args.radius_noise_mm, name="--radius-noise-mm")
    elif args.command == "helix":
        if args.height is not None:
            _require_positive(parser, args.height, name="--height")
        _require_positive(parser, args.base_radius, name="--base-radius")
        _require_non_negative(parser, args.radial_amp, name="--radial-amp")
        _require_positive(parser, args.turns, name="--turns")
        _require_positive(parser, args.tube_radius, name="--tube-radius")
        _require_non_negative(parser, args.ridge_amp, name="--ridge-amp")
        _require_non_negative(parser, args.angle_jitter_deg, name="--angle-jitter-deg")
        _require_non_negative(parser, args.radius_noise_mm, name="--radius-noise-mm")
    elif args.command == "field":
        _require_positive(parser, args.resolution, name="--resolution")
        if args.resolution < 8:
            parser.error("--resolution must be >= 8.")
        _require_non_negative(parser, args.level, name="--level")
        _require_positive(parser, args.scale, name="--scale")
    elif args.command == "ssynth":
        _require_positive(parser, args.max_events, name="--max-events")
        if not 0.0 <= args.onset_threshold <= 1.0:
            parser.error("--onset-threshold must be in [0, 1].")
    elif args.command == "seed-sweep":
        _require_positive(parser, args.sr, name="--sr")
        _require_positive(parser, args.hop, name="--hop")
        _require_positive(parser, args.seed_count, name="--seed-count")
        _require_positive(parser, args.seed_step, name="--seed-step")
        if args.generator == "terrain":
            if args.width is not None:
                _require_positive(parser, args.width, name="--width")
            _require_positive(parser, args.depth, name="--depth")
            if args.height is not None:
                _require_positive(parser, args.height, name="--height")
            _require_non_negative(parser, args.base, name="--base")
            _require_non_negative(parser, args.texture_noise_mm, name="--texture-noise-mm")
        elif args.generator == "ribbon":
            _require_positive(parser, args.length, name="--length")
            if args.width is not None:
                _require_positive(parser, args.width, name="--width")
            _require_positive(parser, args.thickness, name="--thickness")
            if args.height is not None:
                _require_positive(parser, args.height, name="--height")
            _require_non_negative(parser, args.lateral, name="--lateral")
            _require_non_negative(parser, args.wobble_mm, name="--wobble-mm")
        elif args.generator == "vessel":
            if args.height is not None:
                _require_positive(parser, args.height, name="--height")
            _require_positive(parser, args.base_radius, name="--base-radius")
            _require_non_negative(parser, args.radial_amp, name="--radial-amp")
            _require_positive(parser, args.layers, name="--layers")
            if args.layers < 2:
                parser.error("--layers must be >= 2.")
            _require_non_negative(parser, args.ridge_amp, name="--ridge-amp")
            _require_non_negative(parser, args.angle_jitter_deg, name="--angle-jitter-deg")
            _require_non_negative(parser, args.radius_noise_mm, name="--radius-noise-mm")
        elif args.generator == "helix":
            if args.height is not None:
                _require_positive(parser, args.height, name="--height")
            _require_positive(parser, args.base_radius, name="--base-radius")
            _require_non_negative(parser, args.radial_amp, name="--radial-amp")
            _require_positive(parser, args.turns, name="--turns")
            _require_positive(parser, args.tube_radius, name="--tube-radius")
            _require_non_negative(parser, args.ridge_amp, name="--ridge-amp")
            _require_non_negative(parser, args.angle_jitter_deg, name="--angle-jitter-deg")
            _require_non_negative(parser, args.radius_noise_mm, name="--radius-noise-mm")
        elif args.generator == "field":
            _require_positive(parser, args.resolution, name="--resolution")
            if args.resolution < 8:
                parser.error("--resolution must be >= 8.")
            _require_non_negative(parser, args.level, name="--level")
            _require_positive(parser, args.scale, name="--scale")
        elif args.generator == "ssynth":
            _require_positive(parser, args.max_events, name="--max-events")
            if not 0.0 <= args.onset_threshold <= 1.0:
                parser.error("--onset-threshold must be in [0, 1].")
    elif args.command == "param-sweep":
        _require_positive(parser, args.sr, name="--sr")
        _require_positive(parser, args.hop, name="--hop")
        _validate_param_sweep_spec(parser, args)
        if args.generator == "terrain":
            if args.width is not None:
                _require_positive(parser, args.width, name="--width")
            _require_positive(parser, args.depth, name="--depth")
            if args.height is not None:
                _require_positive(parser, args.height, name="--height")
            _require_non_negative(parser, args.base, name="--base")
            _require_non_negative(parser, args.texture_noise_mm, name="--texture-noise-mm")
        elif args.generator == "ribbon":
            _require_positive(parser, args.length, name="--length")
            if args.width is not None:
                _require_positive(parser, args.width, name="--width")
            _require_positive(parser, args.thickness, name="--thickness")
            if args.height is not None:
                _require_positive(parser, args.height, name="--height")
            _require_non_negative(parser, args.lateral, name="--lateral")
            _require_non_negative(parser, args.wobble_mm, name="--wobble-mm")
        elif args.generator == "vessel":
            if args.height is not None:
                _require_positive(parser, args.height, name="--height")
            _require_positive(parser, args.base_radius, name="--base-radius")
            _require_non_negative(parser, args.radial_amp, name="--radial-amp")
            _require_positive(parser, args.layers, name="--layers")
            if args.layers < 2:
                parser.error("--layers must be >= 2.")
            _require_non_negative(parser, args.ridge_amp, name="--ridge-amp")
            _require_non_negative(parser, args.angle_jitter_deg, name="--angle-jitter-deg")
            _require_non_negative(parser, args.radius_noise_mm, name="--radius-noise-mm")
        elif args.generator == "helix":
            if args.height is not None:
                _require_positive(parser, args.height, name="--height")
            _require_positive(parser, args.base_radius, name="--base-radius")
            _require_non_negative(parser, args.radial_amp, name="--radial-amp")
            _require_positive(parser, args.turns, name="--turns")
            _require_positive(parser, args.tube_radius, name="--tube-radius")
            _require_non_negative(parser, args.ridge_amp, name="--ridge-amp")
            _require_non_negative(parser, args.angle_jitter_deg, name="--angle-jitter-deg")
            _require_non_negative(parser, args.radius_noise_mm, name="--radius-noise-mm")
        elif args.generator == "field":
            _require_positive(parser, args.resolution, name="--resolution")
            if args.resolution < 8:
                parser.error("--resolution must be >= 8.")
            _require_non_negative(parser, args.level, name="--level")
            _require_positive(parser, args.scale, name="--scale")
        elif args.generator == "ssynth":
            _require_positive(parser, args.max_events, name="--max-events")
            if not 0.0 <= args.onset_threshold <= 1.0:
                parser.error("--onset-threshold must be in [0, 1].")


def _seed_series(start: int, count: int, step: int) -> list[int]:
    return [start + (i * step) for i in range(count)]


def _seed_label(seed: int) -> str:
    return str(seed).replace("-", "neg")


def _value_label(value: Any) -> str:
    return (
        str(value)
        .replace("-", "neg")
        .replace(".", "p")
        .replace("/", "_")
        .replace(" ", "_")
    )


def _sweep_output_path(out_dir: Path, prefix: str, generator: str, seed: int) -> Path:
    ext = ".es" if generator == "ssynth" else ".obj"
    return out_dir / f"{prefix}_{generator}_seed{_seed_label(seed)}{ext}"


def _param_sweep_output_path(out_dir: Path, prefix: str, generator: str, param: str, value: Any) -> Path:
    ext = ".es" if generator == "ssynth" else ".obj"
    return out_dir / f"{prefix}_{generator}_{param}{_value_label(value)}{ext}"


def _run_generator(
    *,
    generator: str,
    features: Any,
    args: argparse.Namespace,
    out_path: Path,
    seed: int,
) -> dict[str, Any]:
    if generator == "terrain":
        return write_terrain(
            features,
            out_path,
            width_mm=args.width if args.width is not None else 90.0,
            depth_mm=args.depth,
            height_mm=args.height if args.height is not None else 14.0,
            base_mm=args.base,
            texture_noise_mm=args.texture_noise_mm,
            seed=seed,
        )
    if generator == "ribbon":
        return write_ribbon(
            features,
            out_path,
            length_mm=args.length,
            width_mm=args.width if args.width is not None else 8.0,
            thickness_mm=args.thickness,
            height_mm=args.height if args.height is not None else 32.0,
            lateral_mm=args.lateral,
            twist=args.twist,
            wobble_mm=args.wobble_mm,
            seed=seed,
        )
    if generator == "vessel":
        return write_vessel(
            features,
            out_path,
            height_mm=args.height if args.height is not None else 90.0,
            base_radius_mm=args.base_radius,
            radial_amp_mm=args.radial_amp,
            layers=args.layers,
            ridge_amp_mm=args.ridge_amp,
            angle_jitter_deg=args.angle_jitter_deg,
            radius_noise_mm=args.radius_noise_mm,
            close_top=args.close_top,
            seed=seed,
        )
    if generator == "helix":
        return write_helix(
            features,
            out_path,
            height_mm=args.height if args.height is not None else 120.0,
            base_radius_mm=args.base_radius,
            radial_amp_mm=args.radial_amp,
            turns=args.turns,
            tube_radius_mm=args.tube_radius,
            ridge_amp_mm=args.ridge_amp,
            angle_jitter_deg=args.angle_jitter_deg,
            radius_noise_mm=args.radius_noise_mm,
            seed=seed,
        )
    if generator == "field":
        return write_implicit_field(
            features,
            out_path,
            resolution=args.resolution,
            level=args.level,
            scale_mm=args.scale,
            seed=seed,
        )
    if generator == "ssynth":
        return write_structuresynth_grammar(
            features,
            out_path,
            seed=seed,
            template=args.template,
            max_events=args.max_events,
            onset_threshold=args.onset_threshold,
        )
    raise ValueError(f"Unsupported generator: {generator}")


def _build_comparison_row(
    *,
    generator: str,
    param: str,
    value: Any,
    seed: int,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    mesh = manifest.get("mesh", {})
    outputs = manifest.get("outputs", {})
    structuresynth = manifest.get("structuresynth", {})
    summary = structuresynth.get("summary", {})
    row: dict[str, Any] = {
        "generator": generator,
        "param": param,
        "value": value,
        "seed": seed,
        "seed_usage": manifest.get("seed_usage"),
        "manifest": outputs.get("manifest"),
        "obj": outputs.get("obj"),
        "eisenscript": outputs.get("eisenscript"),
        "vertex_count": mesh.get("vertex_count"),
        "face_count": mesh.get("face_count"),
        "extent_x": None,
        "extent_y": None,
        "extent_z": None,
        "warning_count": len(mesh.get("warnings", [])),
        "template": structuresynth.get("template"),
        "event_count_written": structuresynth.get("event_count_written"),
        "onset_density": summary.get("onset_density"),
    }
    extents = mesh.get("extents") or []
    if len(extents) == 3:
        row["extent_x"], row["extent_y"], row["extent_z"] = extents
    return row


def _write_comparison_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    fieldnames = [
        "generator",
        "param",
        "value",
        "seed",
        "seed_usage",
        "manifest",
        "obj",
        "eisenscript",
        "vertex_count",
        "face_count",
        "extent_x",
        "extent_y",
        "extent_z",
        "warning_count",
        "template",
        "event_count_written",
        "onset_density",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def generate_sample(out: str | Path, *, seconds: float = 4.0, sr: int = 22050) -> Path:
    """Generate a tiny sine-sweep-ish WAV for smoke testing."""
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    t = np.linspace(0, seconds, int(sr * seconds), endpoint=False)
    sweep = np.sin(2 * np.pi * (110 + 330 * (t / seconds)) * t)
    pulse = (np.sin(2 * np.pi * 2.0 * t) > 0.82).astype(float) * 0.4
    y = (0.65 * sweep + pulse) * 0.6
    wavfile.write(out_path, sr, np.asarray(y * 32767, dtype=np.int16))
    return out_path


def add_audio_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("audio", help="Input audio path")
    parser.add_argument("--out", required=True, help="Output OBJ path")
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Deterministic seed. Used by some generators; always recorded in manifest.",
    )
    parser.add_argument("--sr", type=int, default=22050, help="Analysis sample rate")
    parser.add_argument("--hop", type=int, default=512, help="Analysis hop length")
    parser.add_argument("--csv", default=None, help="Optional feature CSV output path")


def main() -> None:
    parser = argparse.ArgumentParser(prog="dspform", description="Generate mesh forms from audio/DSP features.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_sample = sub.add_parser("sample", help="Generate a small test WAV")
    p_sample.add_argument("--out", required=True)
    p_sample.add_argument("--seconds", type=float, default=4.0)
    p_sample.add_argument("--sr", type=int, default=22050)

    p_terrain = sub.add_parser("terrain", help="Generate a spectrogram terrain tile")
    add_audio_common(p_terrain)
    p_terrain.add_argument("--width", type=float, default=90.0)
    p_terrain.add_argument("--depth", type=float, default=60.0)
    p_terrain.add_argument("--height", type=float, default=14.0)
    p_terrain.add_argument("--base", type=float, default=2.0)
    p_terrain.add_argument("--texture-noise-mm", type=float, default=0.0, help="Seeded Z-noise amplitude for terrain texture")

    p_ribbon = sub.add_parser("ribbon", help="Generate a swept waveform/feature ribbon")
    add_audio_common(p_ribbon)
    p_ribbon.add_argument("--length", type=float, default=120.0)
    p_ribbon.add_argument("--width", type=float, default=8.0)
    p_ribbon.add_argument("--thickness", type=float, default=1.2)
    p_ribbon.add_argument("--height", type=float, default=32.0)
    p_ribbon.add_argument("--lateral", type=float, default=24.0)
    p_ribbon.add_argument("--twist", type=float, default=0.0)
    p_ribbon.add_argument("--wobble-mm", type=float, default=0.0, help="Random lateral jitter amplitude in millimeters")

    p_vessel = sub.add_parser("vessel", help="Generate a circular vessel from audio features")
    add_audio_common(p_vessel)
    p_vessel.add_argument("--height", type=float, default=90.0)
    p_vessel.add_argument("--base-radius", type=float, default=20.0)
    p_vessel.add_argument("--radial-amp", type=float, default=12.0)
    p_vessel.add_argument("--layers", type=int, default=48)
    p_vessel.add_argument("--ridge-amp", type=float, default=3.0)
    p_vessel.add_argument("--angle-jitter-deg", type=float, default=0.0, help="Seeded angular jitter amplitude in degrees")
    p_vessel.add_argument("--radius-noise-mm", type=float, default=0.0, help="Seeded radial noise amplitude in millimeters")
    p_vessel.add_argument("--close-top", action="store_true")

    p_helix = sub.add_parser("helix", help="Generate a signal-driven helical tube from audio features")
    add_audio_common(p_helix)
    p_helix.add_argument("--height", type=float, default=120.0)
    p_helix.add_argument("--base-radius", type=float, default=24.0)
    p_helix.add_argument("--radial-amp", type=float, default=10.0)
    p_helix.add_argument("--turns", type=float, default=3.5)
    p_helix.add_argument("--tube-radius", type=float, default=4.0)
    p_helix.add_argument("--ridge-amp", type=float, default=1.6)
    p_helix.add_argument("--angle-jitter-deg", type=float, default=0.0, help="Seeded angular jitter amplitude in degrees")
    p_helix.add_argument("--radius-noise-mm", type=float, default=0.0, help="Seeded radial noise amplitude in millimeters")

    p_field = sub.add_parser("field", help="Generate an implicit-field form using marching cubes")
    add_audio_common(p_field)
    p_field.add_argument("--resolution", type=int, default=48)
    p_field.add_argument("--level", type=float, default=0.35)
    p_field.add_argument("--scale", type=float, default=80.0)

    p_ssynth = sub.add_parser("ssynth", help="Generate a StructureSynth/EisenScript grammar score from audio")
    p_ssynth.add_argument("audio", help="Input audio path")
    p_ssynth.add_argument("--out", required=True, help="Output .es / EisenScript path")
    p_ssynth.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Deterministic seed used for grammar generation and recorded in manifest",
    )
    p_ssynth.add_argument("--sr", type=int, default=22050, help="Analysis sample rate")
    p_ssynth.add_argument("--hop", type=int, default=512, help="Analysis hop length")
    p_ssynth.add_argument("--csv", default=None, help="Optional feature CSV output path")
    p_ssynth.add_argument(
        "--template",
        default="onset-lattice",
        choices=["onset-lattice", "radial-burst", "helix-coil", "helix-thread", "helix-vine", "chrono-body", "chrono-body-dense"],
        help="Grammar template",
    )
    p_ssynth.add_argument("--max-events", type=int, default=24, help="Maximum onset/event calls written into the grammar")
    p_ssynth.add_argument("--onset-threshold", type=float, default=0.62, help="Normalized onset threshold for event extraction")

    p_sweep = sub.add_parser("seed-sweep", help="Generate a family of outputs across seeds")
    p_sweep.add_argument("audio", help="Input audio path")
    p_sweep.add_argument("--generator", required=True, choices=["terrain", "ribbon", "vessel", "helix", "field", "ssynth"])
    p_sweep.add_argument("--out-dir", required=True, help="Output directory for generated family")
    p_sweep.add_argument("--name-prefix", default=None, help="Output filename prefix (default: input audio stem)")
    p_sweep.add_argument("--seed-start", type=int, default=0)
    p_sweep.add_argument("--seed-count", type=int, default=8)
    p_sweep.add_argument("--seed-step", type=int, default=1)
    p_sweep.add_argument("--sr", type=int, default=22050, help="Analysis sample rate")
    p_sweep.add_argument("--hop", type=int, default=512, help="Analysis hop length")
    p_sweep.add_argument("--csv", default=None, help="Optional feature CSV output path (written once)")
    p_sweep.add_argument("--width", type=float, default=None)
    p_sweep.add_argument("--depth", type=float, default=60.0)
    p_sweep.add_argument("--height", type=float, default=None)
    p_sweep.add_argument("--base", type=float, default=2.0)
    p_sweep.add_argument("--texture-noise-mm", type=float, default=0.0)
    p_sweep.add_argument("--length", type=float, default=120.0)
    p_sweep.add_argument("--thickness", type=float, default=1.2)
    p_sweep.add_argument("--lateral", type=float, default=24.0)
    p_sweep.add_argument("--twist", type=float, default=0.0)
    p_sweep.add_argument("--wobble-mm", type=float, default=0.0)
    p_sweep.add_argument("--base-radius", type=float, default=20.0)
    p_sweep.add_argument("--radial-amp", type=float, default=12.0)
    p_sweep.add_argument("--layers", type=int, default=48)
    p_sweep.add_argument("--turns", type=float, default=3.5)
    p_sweep.add_argument("--tube-radius", type=float, default=4.0)
    p_sweep.add_argument("--ridge-amp", type=float, default=3.0)
    p_sweep.add_argument("--angle-jitter-deg", type=float, default=0.0)
    p_sweep.add_argument("--radius-noise-mm", type=float, default=0.0)
    p_sweep.add_argument("--close-top", action="store_true")
    p_sweep.add_argument("--resolution", type=int, default=48)
    p_sweep.add_argument("--level", type=float, default=0.35)
    p_sweep.add_argument("--scale", type=float, default=80.0)
    p_sweep.add_argument("--template", default="onset-lattice", choices=["onset-lattice", "radial-burst", "helix-coil", "helix-thread", "helix-vine", "chrono-body", "chrono-body-dense"])
    p_sweep.add_argument("--max-events", type=int, default=24)
    p_sweep.add_argument("--onset-threshold", type=float, default=0.62)

    p_param_sweep = sub.add_parser("param-sweep", help="Generate a family by varying one parameter")
    p_param_sweep.add_argument("audio", help="Input audio path")
    p_param_sweep.add_argument("--generator", required=True, choices=["terrain", "ribbon", "vessel", "helix", "field", "ssynth"])
    p_param_sweep.add_argument("--param", required=True, help="Parameter name to vary")
    p_param_sweep.add_argument("--values", required=True, help="Comma-separated values for the parameter sweep")
    p_param_sweep.add_argument("--out-dir", required=True, help="Output directory for generated family")
    p_param_sweep.add_argument("--name-prefix", default=None, help="Output filename prefix (default: input audio stem)")
    p_param_sweep.add_argument("--seed", type=int, default=0, help="Fixed seed used for every sweep entry")
    p_param_sweep.add_argument("--sr", type=int, default=22050, help="Analysis sample rate")
    p_param_sweep.add_argument("--hop", type=int, default=512, help="Analysis hop length")
    p_param_sweep.add_argument("--csv", default=None, help="Optional feature CSV output path (written once)")
    p_param_sweep.add_argument("--width", type=float, default=None)
    p_param_sweep.add_argument("--depth", type=float, default=60.0)
    p_param_sweep.add_argument("--height", type=float, default=None)
    p_param_sweep.add_argument("--base", type=float, default=2.0)
    p_param_sweep.add_argument("--texture-noise-mm", type=float, default=0.0)
    p_param_sweep.add_argument("--length", type=float, default=120.0)
    p_param_sweep.add_argument("--thickness", type=float, default=1.2)
    p_param_sweep.add_argument("--lateral", type=float, default=24.0)
    p_param_sweep.add_argument("--twist", type=float, default=0.0)
    p_param_sweep.add_argument("--wobble-mm", type=float, default=0.0)
    p_param_sweep.add_argument("--base-radius", type=float, default=20.0)
    p_param_sweep.add_argument("--radial-amp", type=float, default=12.0)
    p_param_sweep.add_argument("--layers", type=int, default=48)
    p_param_sweep.add_argument("--turns", type=float, default=3.5)
    p_param_sweep.add_argument("--tube-radius", type=float, default=4.0)
    p_param_sweep.add_argument("--ridge-amp", type=float, default=3.0)
    p_param_sweep.add_argument("--angle-jitter-deg", type=float, default=0.0)
    p_param_sweep.add_argument("--radius-noise-mm", type=float, default=0.0)
    p_param_sweep.add_argument("--close-top", action="store_true")
    p_param_sweep.add_argument("--resolution", type=int, default=48)
    p_param_sweep.add_argument("--level", type=float, default=0.35)
    p_param_sweep.add_argument("--scale", type=float, default=80.0)
    p_param_sweep.add_argument("--template", default="onset-lattice", choices=["onset-lattice", "radial-burst", "helix-coil", "helix-thread", "helix-vine", "chrono-body", "chrono-body-dense"])
    p_param_sweep.add_argument("--max-events", type=int, default=24)
    p_param_sweep.add_argument("--onset-threshold", type=float, default=0.62)

    p_contact = sub.add_parser("contact-sheet", help="Render a contact sheet from a sweep index JSON")
    p_contact.add_argument("index", help="Path to *_seed_sweep.json or *_param_sweep.json")
    p_contact.add_argument("--out", required=True, help="Output PNG path")
    p_contact.add_argument("--cols", type=int, default=4)
    p_contact.add_argument("--tile-width", type=float, default=4.0)
    p_contact.add_argument("--tile-height", type=float, default=3.4)

    args = parser.parse_args()
    _validate_args(parser, args)

    if args.command == "sample":
        path = generate_sample(args.out, seconds=args.seconds, sr=args.sr)
        print(f"wrote {path}")
        return

    if args.command == "contact-sheet":
        out_path = build_contact_sheet(
            args.index,
            args.out,
            cols=args.cols,
            tile_width=args.tile_width,
            tile_height=args.tile_height,
        )
        print(f"wrote {out_path}")
        return

    if args.command == "seed-sweep":
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        features = load_audio_features(args.audio, sr=args.sr, hop_length=args.hop)
        if args.csv:
            csv_path = save_feature_csv(features, args.csv)
            print(f"wrote {csv_path}")
        prefix = args.name_prefix or Path(args.audio).stem
        seeds = _seed_series(args.seed_start, args.seed_count, args.seed_step)
        records: list[dict[str, Any]] = []
        for seed in seeds:
            out_path = _sweep_output_path(out_dir, prefix, args.generator, seed)
            manifest = _run_generator(
                generator=args.generator,
                features=features,
                args=args,
                out_path=out_path,
                seed=seed,
            )
            record: dict[str, Any] = {"seed": seed, "manifest": manifest["outputs"]["manifest"]}
            if "obj" in manifest["outputs"]:
                record["obj"] = manifest["outputs"]["obj"]
                print(f"wrote {manifest['outputs']['obj']}")
            if "eisenscript" in manifest["outputs"]:
                record["eisenscript"] = manifest["outputs"]["eisenscript"]
                print(f"wrote {manifest['outputs']['eisenscript']}")
            print(f"wrote {manifest['outputs']['manifest']}")
            records.append(record)
        sweep_manifest = out_dir / f"{prefix}_{args.generator}_seed_sweep.json"
        write_json(
            sweep_manifest,
            {
                "generator": args.generator,
                "audio_path": str(args.audio),
                "sr": args.sr,
                "hop": args.hop,
                "seed_start": args.seed_start,
                "seed_count": args.seed_count,
                "seed_step": args.seed_step,
                "seeds": seeds,
                "records": records,
            },
        )
        print(f"wrote {sweep_manifest}")
        return

    if args.command == "param-sweep":
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        features = load_audio_features(args.audio, sr=args.sr, hop_length=args.hop)
        if args.csv:
            csv_path = save_feature_csv(features, args.csv)
            print(f"wrote {csv_path}")
        prefix = args.name_prefix or Path(args.audio).stem
        values = _parse_param_sweep_values(args.generator, args.param, args.values)
        records: list[dict[str, Any]] = []
        comparison_rows: list[dict[str, Any]] = []
        for value in values:
            variant_args = argparse.Namespace(**vars(args))
            setattr(variant_args, args.param, value)
            out_path = _param_sweep_output_path(out_dir, prefix, args.generator, args.param, value)
            manifest = _run_generator(
                generator=args.generator,
                features=features,
                args=variant_args,
                out_path=out_path,
                seed=args.seed,
            )
            record: dict[str, Any] = {
                "param": args.param,
                "value": value,
                "seed": args.seed,
                "manifest": manifest["outputs"]["manifest"],
            }
            if "obj" in manifest["outputs"]:
                record["obj"] = manifest["outputs"]["obj"]
                print(f"wrote {manifest['outputs']['obj']}")
            if "eisenscript" in manifest["outputs"]:
                record["eisenscript"] = manifest["outputs"]["eisenscript"]
                print(f"wrote {manifest['outputs']['eisenscript']}")
            print(f"wrote {manifest['outputs']['manifest']}")
            records.append(record)
            comparison_rows.append(
                _build_comparison_row(
                    generator=args.generator,
                    param=args.param,
                    value=value,
                    seed=args.seed,
                    manifest=manifest,
                )
            )
        comparison_csv = out_dir / f"{prefix}_{args.generator}_{args.param}_comparison.csv"
        _write_comparison_csv(comparison_csv, comparison_rows)
        print(f"wrote {comparison_csv}")
        sweep_manifest = out_dir / f"{prefix}_{args.generator}_{args.param}_param_sweep.json"
        write_json(
            sweep_manifest,
            {
                "generator": args.generator,
                "audio_path": str(args.audio),
                "param": args.param,
                "values": values,
                "seed": args.seed,
                "sr": args.sr,
                "hop": args.hop,
                "comparison_csv": str(comparison_csv),
                "records": records,
            },
        )
        print(f"wrote {sweep_manifest}")
        return

    features = load_audio_features(args.audio, sr=args.sr, hop_length=args.hop)
    if args.csv:
        csv_path = save_feature_csv(features, args.csv)
        print(f"wrote {csv_path}")

    if args.command == "terrain":
        manifest = write_terrain(
            features,
            args.out,
            width_mm=args.width,
            depth_mm=args.depth,
            height_mm=args.height,
            base_mm=args.base,
            texture_noise_mm=args.texture_noise_mm,
            seed=args.seed,
        )
    elif args.command == "ribbon":
        manifest = write_ribbon(
            features,
            args.out,
            length_mm=args.length,
            width_mm=args.width,
            thickness_mm=args.thickness,
            height_mm=args.height,
            lateral_mm=args.lateral,
            twist=args.twist,
            wobble_mm=args.wobble_mm,
            seed=args.seed,
        )
    elif args.command == "vessel":
        manifest = write_vessel(
            features,
            args.out,
            height_mm=args.height,
            base_radius_mm=args.base_radius,
            radial_amp_mm=args.radial_amp,
            layers=args.layers,
            ridge_amp_mm=args.ridge_amp,
            angle_jitter_deg=args.angle_jitter_deg,
            radius_noise_mm=args.radius_noise_mm,
            close_top=args.close_top,
            seed=args.seed,
        )
    elif args.command == "helix":
        manifest = write_helix(
            features,
            args.out,
            height_mm=args.height,
            base_radius_mm=args.base_radius,
            radial_amp_mm=args.radial_amp,
            turns=args.turns,
            tube_radius_mm=args.tube_radius,
            ridge_amp_mm=args.ridge_amp,
            angle_jitter_deg=args.angle_jitter_deg,
            radius_noise_mm=args.radius_noise_mm,
            seed=args.seed,
        )
    elif args.command == "field":
        manifest = write_implicit_field(
            features,
            args.out,
            resolution=args.resolution,
            level=args.level,
            scale_mm=args.scale,
            seed=args.seed,
        )
    elif args.command == "ssynth":
        manifest = write_structuresynth_grammar(
            features,
            args.out,
            seed=args.seed,
            template=args.template,
            max_events=args.max_events,
            onset_threshold=args.onset_threshold,
        )
    else:
        raise ValueError(f"Unknown command: {args.command}")

    if "obj" in manifest["outputs"]:
        print(f"wrote {manifest['outputs']['obj']}")
    if "eisenscript" in manifest["outputs"]:
        print(f"wrote {manifest['outputs']['eisenscript']}")
    print(f"wrote {manifest['outputs']['manifest']}")
    warnings = manifest.get("mesh", {}).get("warnings", [])
    if warnings:
        print("warnings:")
        for warning in warnings:
            print(f"  - {warning}")


if __name__ == "__main__":
    main()
