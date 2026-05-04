from __future__ import annotations

from pathlib import Path

from dspform.audio_features import load_audio_features
from dspform.cli import generate_sample
from dspform.generators.growth_body import growth_body_mesh
from dspform.generators.helix import helix_mesh
from dspform.generators.ribbon import ribbon_mesh
from dspform.generators.terrain import terrain_mesh
from dspform.generators.vessel import vessel_mesh
from dspform.structuresynth import generate_eisenscript


def test_generators_produce_vertices_and_faces(tmp_path: Path) -> None:
    audio_path = generate_sample(tmp_path / "sample.wav", seconds=1.0, sr=22050)
    features = load_audio_features(audio_path, sr=22050, hop_length=512, max_bins=24)

    for factory in [terrain_mesh, ribbon_mesh, vessel_mesh, helix_mesh, growth_body_mesh]:
        vertices, faces = factory(features)
        assert len(vertices) > 0
        assert len(faces) > 0
        assert faces.max() < len(vertices)


def test_ribbon_is_deterministic_when_wobble_disabled(tmp_path: Path) -> None:
    audio_path = generate_sample(tmp_path / "sample.wav", seconds=1.0, sr=22050)
    features = load_audio_features(audio_path, sr=22050, hop_length=512, max_bins=24)
    a_vertices, a_faces = ribbon_mesh(features, seed=1, wobble_mm=0.0)
    b_vertices, b_faces = ribbon_mesh(features, seed=99, wobble_mm=0.0)
    assert (a_vertices == b_vertices).all()
    assert (a_faces == b_faces).all()

def test_structuresynth_generator_writes_eisenscript(tmp_path: Path) -> None:
    audio_path = generate_sample(tmp_path / "sample.wav", seconds=1.0, sr=22050)
    features = load_audio_features(audio_path, sr=22050, hop_length=512, max_bins=24)
    grammar, metadata = generate_eisenscript(features, seed=7, max_events=8)
    assert "set seed 7" in grammar
    assert "rule start" in grammar
    assert "eventMid" in grammar or "eventLow" in grammar or "eventHigh" in grammar
    assert metadata["template"] == "onset-lattice"
    assert metadata["event_count_written"] <= 8
