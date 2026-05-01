from __future__ import annotations

import argparse

import pytest

from dspform.cli import _parse_param_sweep_values, _validate_args


def _parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(prog="dspform-test")


def test_validate_rejects_negative_ribbon_wobble() -> None:
    args = argparse.Namespace(
        command="ribbon",
        sr=22050,
        hop=512,
        length=120.0,
        width=8.0,
        thickness=1.2,
        height=32.0,
        lateral=24.0,
        wobble_mm=-0.1,
    )
    with pytest.raises(SystemExit):
        _validate_args(_parser(), args)


def test_validate_rejects_out_of_range_onset_threshold() -> None:
    args = argparse.Namespace(
        command="ssynth",
        sr=22050,
        hop=512,
        max_events=24,
        onset_threshold=1.2,
    )
    with pytest.raises(SystemExit):
        _validate_args(_parser(), args)


def test_validate_accepts_seeded_vessel_controls() -> None:
    args = argparse.Namespace(
        command="vessel",
        sr=22050,
        hop=512,
        height=90.0,
        base_radius=20.0,
        radial_amp=12.0,
        layers=48,
        ridge_amp=3.0,
        angle_jitter_deg=7.5,
        radius_noise_mm=0.9,
    )
    _validate_args(_parser(), args)


def test_validate_rejects_non_positive_seed_sweep_count() -> None:
    args = argparse.Namespace(
        command="seed-sweep",
        generator="terrain",
        sr=22050,
        hop=512,
        seed_count=0,
        seed_step=1,
        width=None,
        depth=60.0,
        height=None,
        base=2.0,
        texture_noise_mm=0.0,
    )
    with pytest.raises(SystemExit):
        _validate_args(_parser(), args)


def test_validate_accepts_seed_sweep_for_ssynth() -> None:
    args = argparse.Namespace(
        command="seed-sweep",
        generator="ssynth",
        sr=22050,
        hop=512,
        seed_count=8,
        seed_step=1,
        max_events=24,
        onset_threshold=0.62,
    )
    _validate_args(_parser(), args)


def test_parse_param_sweep_values_coerces_numeric_values() -> None:
    values = _parse_param_sweep_values("terrain", "texture_noise_mm", "0.0,0.2,0.6")
    assert values == [0.0, 0.2, 0.6]


def test_parse_param_sweep_values_rejects_unknown_param() -> None:
    with pytest.raises(ValueError):
        _parse_param_sweep_values("terrain", "twist", "0.0,1.0")


def test_validate_rejects_param_sweep_with_single_value() -> None:
    args = argparse.Namespace(
        command="param-sweep",
        generator="terrain",
        param="texture_noise_mm",
        values="0.4",
        sr=22050,
        hop=512,
        width=None,
        depth=60.0,
        height=None,
        base=2.0,
        texture_noise_mm=0.0,
    )
    with pytest.raises(SystemExit):
        _validate_args(_parser(), args)


def test_validate_accepts_param_sweep_for_ssynth_template() -> None:
    args = argparse.Namespace(
        command="param-sweep",
        generator="ssynth",
        param="template",
        values="onset-lattice,radial-burst",
        sr=22050,
        hop=512,
        max_events=24,
        onset_threshold=0.62,
    )
    _validate_args(_parser(), args)


def test_validate_rejects_non_positive_contact_sheet_cols() -> None:
    args = argparse.Namespace(
        command="contact-sheet",
        cols=0,
        tile_width=4.0,
        tile_height=3.4,
    )
    with pytest.raises(SystemExit):
        _validate_args(_parser(), args)


def test_validate_accepts_contact_sheet_args() -> None:
    args = argparse.Namespace(
        command="contact-sheet",
        cols=4,
        tile_width=4.0,
        tile_height=3.4,
    )
    _validate_args(_parser(), args)
