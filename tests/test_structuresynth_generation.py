from __future__ import annotations

import re
from pathlib import Path

import numpy as np

from dspform.audio_features import AudioFeatures
from dspform.structuresynth import generate_eisenscript


RULE_DEF = re.compile(r"^rule\s+([A-Za-z][A-Za-z0-9]*)\b")
RULE_CALL = re.compile(r"\}\s+([A-Za-z][A-Za-z0-9]*)\s*$")
ALLOWED_BUILTINS = {"sphere", "box", "grid", "line", "dot", "cylinder", "mesh", "cylindermesh"}


def _fake_features() -> AudioFeatures:
    frames = 20
    return AudioFeatures(
        source_path=Path("fake.wav"),
        sample_rate=22050,
        duration_seconds=2.0,
        times=np.linspace(0.0, 2.0, frames),
        rms=np.linspace(0.1, 1.0, frames),
        centroid=np.linspace(1.0, 0.0, frames),
        bandwidth=np.sin(np.linspace(0.0, np.pi, frames)),
        onset=np.array([0, .1, .8, .2, 0, .9, .1, 0, .7, .1, 0, .1, .95, .1, 0, 0, .65, .1, 0, 0]),
        spectrogram_db=np.zeros((8, frames)),
    )


def test_generated_eisenscript_uses_conservative_rule_names() -> None:
    grammar, _metadata = generate_eisenscript(_fake_features(), seed=42, max_events=5)
    assert "start\n" in grammar
    assert "rule start" in grammar
    assert "event_low" not in grammar
    assert "eventMid" in grammar
    assert "{{" not in grammar
    assert "}}" not in grammar


def test_generated_eisenscript_rule_calls_have_definitions() -> None:
    grammar, _metadata = generate_eisenscript(_fake_features(), seed=42, max_events=5)
    defs = set()
    calls = {"start"}

    for line in grammar.splitlines():
        stripped = line.strip()
        match_def = RULE_DEF.match(stripped)
        if match_def:
            defs.add(match_def.group(1))

        match_call = RULE_CALL.search(stripped)
        if match_call:
            target = match_call.group(1)
            if target.lower() not in ALLOWED_BUILTINS:
                calls.add(target)

    assert calls <= defs


def test_radial_burst_template_generates_expected_rules() -> None:
    grammar, metadata = generate_eisenscript(_fake_features(), seed=99, max_events=6, template="radial-burst")
    assert "rule core" in grammar
    assert "rule ring" in grammar
    assert "burstMid" in grammar or "burstLow" in grammar or "burstHigh" in grammar
    assert metadata["template"] == "radial-burst"
    assert metadata["event_count_written"] <= 6
