from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from dspform.audio_features import load_audio_features
from dspform.cli import generate_sample
from dspform.generators.growth_body import growth_body_mesh, write_growth_body
from dspform.gestures import extract_gestures


def test_gesture_extraction_returns_list(tmp_path: Path) -> None:
    audio_path = generate_sample(tmp_path / "sample.wav", seconds=1.0, sr=22050)
    features = load_audio_features(audio_path, sr=22050, hop_length=512, max_bins=24)

    gestures = extract_gestures(features)

    assert isinstance(gestures, list)
    assert all(gesture.kind in {"pulse", "burst", "cluster", "silence"} for gesture in gestures)


def test_growth_body_writes_manifest_with_required_sections(tmp_path: Path) -> None:
    audio_path = Path("audio/samples/sine_sweep.wav")
    if not audio_path.exists():
        audio_path = generate_sample(tmp_path / "sine_sweep.wav", seconds=1.0, sr=22050)
    features = load_audio_features(audio_path, sr=22050, hop_length=512, max_bins=24)

    manifest = write_growth_body(
        features,
        tmp_path / "growth.obj",
        profile="scar",
        memory=0.92,
        event_threshold=0.64,
        branchiness=0.35,
        scar_depth=2.0,
        seed=7,
    )

    manifest_path = Path(manifest["outputs"]["manifest"])
    saved = json.loads(manifest_path.read_text(encoding="utf-8"))
    for key in ["generator", "parameters", "seed_usage", "audio", "mesh", "provenance", "outputs"]:
        assert key in saved
    assert saved["generator"] == "growth_body"
    assert saved["outputs"]["obj"].endswith("growth.obj")
    assert saved["outputs"]["manifest"].endswith("growth.manifest.json")
    assert saved["mesh"]["vertex_count"] > 0
    assert saved["mesh"]["face_count"] > 0


def test_growth_body_is_stable_for_same_seed_and_parameters(tmp_path: Path) -> None:
    audio_path = generate_sample(tmp_path / "sample.wav", seconds=1.0, sr=22050)
    features = load_audio_features(audio_path, sr=22050, hop_length=512, max_bins=24)

    a_vertices, a_faces = growth_body_mesh(
        features,
        profile="relic",
        memory=0.95,
        event_threshold=0.60,
        branchiness=0.4,
        scar_depth=1.8,
        seed=11,
    )
    b_vertices, b_faces = growth_body_mesh(
        features,
        profile="relic",
        memory=0.95,
        event_threshold=0.60,
        branchiness=0.4,
        scar_depth=1.8,
        seed=11,
    )

    assert np.array_equal(a_faces, b_faces)
    assert np.allclose(a_vertices, b_vertices)
