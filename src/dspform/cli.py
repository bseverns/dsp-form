from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from scipy.io import wavfile

from .audio_features import load_audio_features, save_feature_csv
from .generators.implicit_field import write_implicit_field
from .generators.ribbon import write_ribbon
from .generators.terrain import write_terrain
from .generators.vessel import write_vessel
from .structuresynth import write_structuresynth_grammar


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
    parser.add_argument("--seed", type=int, default=0, help="Deterministic seed recorded in manifest")
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

    p_ribbon = sub.add_parser("ribbon", help="Generate a swept waveform/feature ribbon")
    add_audio_common(p_ribbon)
    p_ribbon.add_argument("--length", type=float, default=120.0)
    p_ribbon.add_argument("--width", type=float, default=8.0)
    p_ribbon.add_argument("--thickness", type=float, default=1.2)
    p_ribbon.add_argument("--height", type=float, default=32.0)
    p_ribbon.add_argument("--lateral", type=float, default=24.0)
    p_ribbon.add_argument("--twist", type=float, default=0.0)

    p_vessel = sub.add_parser("vessel", help="Generate a circular vessel from audio features")
    add_audio_common(p_vessel)
    p_vessel.add_argument("--height", type=float, default=90.0)
    p_vessel.add_argument("--base-radius", type=float, default=20.0)
    p_vessel.add_argument("--radial-amp", type=float, default=12.0)
    p_vessel.add_argument("--layers", type=int, default=48)
    p_vessel.add_argument("--ridge-amp", type=float, default=3.0)
    p_vessel.add_argument("--close-top", action="store_true")

    p_field = sub.add_parser("field", help="Generate an implicit-field form using marching cubes")
    add_audio_common(p_field)
    p_field.add_argument("--resolution", type=int, default=48)
    p_field.add_argument("--level", type=float, default=0.35)
    p_field.add_argument("--scale", type=float, default=80.0)

    p_ssynth = sub.add_parser("ssynth", help="Generate a StructureSynth/EisenScript grammar score from audio")
    p_ssynth.add_argument("audio", help="Input audio path")
    p_ssynth.add_argument("--out", required=True, help="Output .es / EisenScript path")
    p_ssynth.add_argument("--seed", type=int, default=0, help="Deterministic seed written into the grammar and manifest")
    p_ssynth.add_argument("--sr", type=int, default=22050, help="Analysis sample rate")
    p_ssynth.add_argument("--hop", type=int, default=512, help="Analysis hop length")
    p_ssynth.add_argument("--csv", default=None, help="Optional feature CSV output path")
    p_ssynth.add_argument("--template", default="onset-lattice", choices=["onset-lattice"], help="Grammar template")
    p_ssynth.add_argument("--max-events", type=int, default=24, help="Maximum onset/event calls written into the grammar")
    p_ssynth.add_argument("--onset-threshold", type=float, default=0.62, help="Normalized onset threshold for event extraction")

    args = parser.parse_args()

    if args.command == "sample":
        path = generate_sample(args.out, seconds=args.seconds, sr=args.sr)
        print(f"wrote {path}")
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
            close_top=args.close_top,
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
