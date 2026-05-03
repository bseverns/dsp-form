from __future__ import annotations

from pathlib import Path

import numpy as np

from dspform.audio_features import AudioFeatures
from dspform.generators.helix import helix_mesh
from dspform.generators.terrain import terrain_mesh
from dspform.generators.vessel import vessel_mesh
from dspform.utils import runtime_provenance


def _fake_features(frames: int = 20) -> AudioFeatures:
    return AudioFeatures(
        source_path=Path("fake.wav"),
        sample_rate=22050,
        duration_seconds=2.0,
        times=np.linspace(0.0, 2.0, frames),
        rms=np.linspace(0.2, 0.9, frames),
        centroid=np.linspace(0.8, 0.1, frames),
        bandwidth=np.sin(np.linspace(0.0, np.pi, frames)),
        onset=np.linspace(0.0, 1.0, frames),
        spectrogram_db=np.tile(np.linspace(-50.0, 0.0, frames), (12, 1)),
    )


def test_terrain_noise_respects_seed_and_defaults() -> None:
    features = _fake_features()
    v0, f0 = terrain_mesh(features, texture_noise_mm=0.0, seed=1)
    v1, f1 = terrain_mesh(features, texture_noise_mm=0.0, seed=999)
    assert np.array_equal(v0, v1)
    assert np.array_equal(f0, f1)

    v2, _ = terrain_mesh(features, texture_noise_mm=0.8, seed=7)
    v3, _ = terrain_mesh(features, texture_noise_mm=0.8, seed=7)
    v4, _ = terrain_mesh(features, texture_noise_mm=0.8, seed=8)
    assert np.array_equal(v2, v3)
    assert not np.array_equal(v2, v4)


def test_vessel_noise_respects_seed_and_defaults() -> None:
    features = _fake_features()
    v0, f0 = vessel_mesh(features, angle_jitter_deg=0.0, radius_noise_mm=0.0, seed=1)
    v1, f1 = vessel_mesh(features, angle_jitter_deg=0.0, radius_noise_mm=0.0, seed=999)
    assert np.array_equal(v0, v1)
    assert np.array_equal(f0, f1)

    v2, _ = vessel_mesh(features, angle_jitter_deg=5.0, radius_noise_mm=0.8, seed=11)
    v3, _ = vessel_mesh(features, angle_jitter_deg=5.0, radius_noise_mm=0.8, seed=11)
    v4, _ = vessel_mesh(features, angle_jitter_deg=5.0, radius_noise_mm=0.8, seed=12)
    assert np.array_equal(v2, v3)
    assert not np.array_equal(v2, v4)


def test_helix_noise_respects_seed_and_defaults() -> None:
    features = _fake_features()
    v0, f0 = helix_mesh(features, angle_jitter_deg=0.0, radius_noise_mm=0.0, seed=1)
    v1, f1 = helix_mesh(features, angle_jitter_deg=0.0, radius_noise_mm=0.0, seed=999)
    assert np.array_equal(v0, v1)
    assert np.array_equal(f0, f1)

    v2, _ = helix_mesh(features, angle_jitter_deg=4.0, radius_noise_mm=0.8, seed=11)
    v3, _ = helix_mesh(features, angle_jitter_deg=4.0, radius_noise_mm=0.8, seed=11)
    v4, _ = helix_mesh(features, angle_jitter_deg=4.0, radius_noise_mm=0.8, seed=12)
    assert np.array_equal(v2, v3)
    assert not np.array_equal(v2, v4)


def test_runtime_provenance_contains_required_keys() -> None:
    data = runtime_provenance()
    assert "python_version" in data
    assert "package_versions" in data
    assert isinstance(data["package_versions"], dict)
