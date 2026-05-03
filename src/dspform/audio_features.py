from __future__ import annotations

from dataclasses import dataclass
from math import gcd
from pathlib import Path
from typing import Any

import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly, stft

from .utils import normalize


@dataclass
class AudioFeatures:
    source_path: Path
    sample_rate: int
    duration_seconds: float
    times: np.ndarray
    rms: np.ndarray
    centroid: np.ndarray
    bandwidth: np.ndarray
    onset: np.ndarray
    spectrogram_db: np.ndarray

    def to_manifest(self) -> dict[str, Any]:
        return {
            "source_path": str(self.source_path),
            "sample_rate": self.sample_rate,
            "duration_seconds": self.duration_seconds,
            "frames": int(len(self.times)),
            "frequency_bins": int(self.spectrogram_db.shape[0]),
            "feature_names": ["rms", "centroid", "bandwidth", "onset", "spectrogram_db"],
        }


def load_audio_features(
    audio_path: str | Path,
    *,
    sr: int | None = 22050,
    hop_length: int = 512,
    n_fft: int = 2048,
    max_bins: int = 96,
) -> AudioFeatures:
    """Load a WAV file and extract starter features.

    This intentionally starts with familiar, high-leverage features:
    RMS = loudness/envelope proxy
    spectral centroid = brightness proxy
    bandwidth = spread/roughness proxy
    onset strength = event/ridge proxy
    spectrogram_db = terrain source
    """
    path = Path(audio_path)
    y, sample_rate = _load_wav_mono(path, sr=sr)
    duration = float(len(y) / sample_rate)

    freqs, times, zxx = stft(
        y,
        fs=sample_rate,
        window="hann",
        nperseg=n_fft,
        noverlap=n_fft - hop_length,
        boundary="zeros",
        padded=True,
    )
    magnitude = np.abs(zxx)
    rms = _frame_rms(y, frame_length=n_fft, hop_length=hop_length, frame_count=magnitude.shape[1])
    centroid, bandwidth = _spectral_shape(freqs, magnitude)
    onset = _spectral_flux(magnitude)
    spec_db = _amplitude_to_db(magnitude)

    # Downsample frequency bins to keep first generated meshes small.
    if spec_db.shape[0] > max_bins:
        idx = np.linspace(0, spec_db.shape[0] - 1, max_bins).astype(int)
        spec_db = spec_db[idx, :]

    # Ensure same frame count across features.
    frame_count = min(len(times), len(rms), len(centroid), len(bandwidth), len(onset), spec_db.shape[1])

    return AudioFeatures(
        source_path=path,
        sample_rate=int(sample_rate),
        duration_seconds=duration,
        times=times[:frame_count],
        rms=rms[:frame_count],
        centroid=centroid[:frame_count],
        bandwidth=bandwidth[:frame_count],
        onset=onset[:frame_count],
        spectrogram_db=spec_db[:, :frame_count],
    )


def _load_wav_mono(path: Path, *, sr: int | None) -> tuple[np.ndarray, int]:
    sample_rate, data = wavfile.read(path)
    y = _to_float_mono(data)
    if sr is not None and sample_rate != sr:
        factor = gcd(sample_rate, sr)
        y = resample_poly(y, up=sr // factor, down=sample_rate // factor)
        sample_rate = sr
    return y.astype(float, copy=False), int(sample_rate)


def _to_float_mono(data: np.ndarray) -> np.ndarray:
    y = np.asarray(data)
    if y.ndim > 1:
        y = y.mean(axis=1)

    if np.issubdtype(y.dtype, np.integer):
        info = np.iinfo(y.dtype)
        scale = max(abs(info.min), abs(info.max))
        return y.astype(float) / scale
    if np.issubdtype(y.dtype, np.floating):
        return y.astype(float, copy=False)
    raise TypeError(f"Unsupported WAV sample dtype: {y.dtype}")


def _frame_rms(y: np.ndarray, *, frame_length: int, hop_length: int, frame_count: int) -> np.ndarray:
    if frame_count <= 0:
        return np.zeros(0, dtype=float)

    pad = frame_length // 2
    padded = np.pad(y, (pad, pad), mode="constant")
    rms = np.zeros(frame_count, dtype=float)
    for i in range(frame_count):
        start = i * hop_length
        frame = padded[start : start + frame_length]
        if len(frame) < frame_length:
            frame = np.pad(frame, (0, frame_length - len(frame)), mode="constant")
        rms[i] = np.sqrt(np.mean(frame * frame))
    return rms


def _spectral_shape(freqs: np.ndarray, magnitude: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    weights = magnitude + 1e-12
    denom = np.sum(weights, axis=0)
    centroid = np.sum(freqs[:, None] * weights, axis=0) / denom
    spread = freqs[:, None] - centroid[None, :]
    bandwidth = np.sqrt(np.sum((spread * spread) * weights, axis=0) / denom)
    return centroid, bandwidth


def _spectral_flux(magnitude: np.ndarray) -> np.ndarray:
    if magnitude.shape[1] == 0:
        return np.zeros(0, dtype=float)
    diffs = np.diff(magnitude, axis=1, prepend=magnitude[:, :1])
    return np.sum(np.maximum(diffs, 0.0), axis=0)


def _amplitude_to_db(magnitude: np.ndarray, *, amin: float = 1e-10) -> np.ndarray:
    ref = max(float(np.max(magnitude)), amin)
    return 20.0 * np.log10(np.maximum(magnitude, amin) / ref)


def feature_table(features: AudioFeatures) -> np.ndarray:
    """Return normalized per-frame features as a numeric table.

    Columns: time, rms, centroid, bandwidth, onset
    """
    return np.column_stack(
        [
            features.times,
            normalize(features.rms),
            normalize(features.centroid),
            normalize(features.bandwidth),
            normalize(features.onset),
        ]
    )


def save_feature_csv(features: AudioFeatures, csv_path: str | Path) -> Path:
    import csv

    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    table = feature_table(features)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time_seconds", "rms_norm", "centroid_norm", "bandwidth_norm", "onset_norm"])
        writer.writerows(table.tolist())
    return path
