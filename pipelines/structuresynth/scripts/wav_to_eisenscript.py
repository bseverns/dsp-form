#!/usr/bin/env python3
"""Small wrapper around the dspform StructureSynth generator.

Usage from repo root:

    python pipelines/structuresynth/scripts/wav_to_eisenscript.py \
      audio/samples/sine_sweep.wav \
      pipelines/structuresynth/grammars/generated/sine_sweep_onset_lattice.es
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from dspform.audio_features import load_audio_features, save_feature_csv  # noqa: E402
from dspform.structuresynth import write_structuresynth_grammar  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an EisenScript grammar from a WAV file.")
    parser.add_argument("audio")
    parser.add_argument("out")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--sr", type=int, default=22050)
    parser.add_argument("--hop", type=int, default=512)
    parser.add_argument("--max-events", type=int, default=24)
    parser.add_argument("--onset-threshold", type=float, default=0.62)
    parser.add_argument("--csv", default=None)
    args = parser.parse_args()

    features = load_audio_features(args.audio, sr=args.sr, hop_length=args.hop)
    if args.csv:
        save_feature_csv(features, args.csv)
    manifest = write_structuresynth_grammar(
        features,
        args.out,
        seed=args.seed,
        max_events=args.max_events,
        onset_threshold=args.onset_threshold,
    )
    print(f"wrote {manifest['outputs']['eisenscript']}")
    print(f"wrote {manifest['outputs']['manifest']}")


if __name__ == "__main__":
    main()
