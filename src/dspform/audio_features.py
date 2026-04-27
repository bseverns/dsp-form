from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

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
    """Load a WAV/AIFF/MP3-compatible file and extract starter features.

    This intentionally starts with familiar, high-leverage features:
    RMS = loudness/envelope proxy
    spectral centroid = brightness proxy
    bandwidth = spread/roughness proxy
    onset strength = event/ridge proxy
    spectrogram_db = terrain source
    """
    import librosa

    path = Path(audio_path)
    y, sample_rate = librosa.load(path, sr=sr, mono=True)
    duration = float(librosa.get_duration(y=y, sr=sample_rate))

    rms = librosa.feature.rms(y=y, frame_length=n_fft, hop_length=hop_length)[0]
    centroid = librosa.feature.spectral_centroid(y=y, sr=sample_rate, n_fft=n_fft, hop_length=hop_length)[0]
    bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sample_rate, n_fft=n_fft, hop_length=hop_length)[0]
    onset = librosa.onset.onset_strength(y=y, sr=sample_rate, hop_length=hop_length)

    stft = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length))
    spec_db = librosa.amplitude_to_db(stft, ref=np.max)

    # Downsample frequency bins to keep first generated meshes small.
    if spec_db.shape[0] > max_bins:
        idx = np.linspace(0, spec_db.shape[0] - 1, max_bins).astype(int)
        spec_db = spec_db[idx, :]

    times = librosa.frames_to_time(np.arange(len(rms)), sr=sample_rate, hop_length=hop_length)

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
