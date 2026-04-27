from __future__ import annotations

from pathlib import Path

from dspform.audio_features import load_audio_features
from dspform.cli import generate_sample
from dspform.generators.ribbon import ribbon_mesh
from dspform.generators.terrain import terrain_mesh
from dspform.generators.vessel import vessel_mesh


def test_generators_produce_vertices_and_faces(tmp_path: Path) -> None:
    audio_path = generate_sample(tmp_path / "sample.wav", seconds=1.0, sr=22050)
    features = load_audio_features(audio_path, sr=22050, hop_length=512, max_bins=24)

    for factory in [terrain_mesh, ribbon_mesh, vessel_mesh]:
        vertices, faces = factory(features)
        assert len(vertices) > 0
        assert len(faces) > 0
        assert faces.max() < len(vertices)
