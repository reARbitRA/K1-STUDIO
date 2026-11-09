# SPEC-003
from __future__ import annotations

import os
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from scipy import ndimage, signal

from .engine import DSPError, bounded, validate_audio
from .filters import RATE, Audio, bell, butter, compress, shelf


def ms_stage(x: Audio, width: float) -> Audio:
    if not len(x):
        return x.copy()
    mid = x.mean(axis=1).astype(np.float64)
    side = (x[:, 0].astype(np.float64) - x[:, 1]) * 0.5
    sos = signal.butter(4, 85, btype="highpass", fs=RATE, output="sos")
    pad = max(0, 32 - len(x))
    padded = np.pad(side, (pad, pad), mode="symmetric") if pad else side
    filtered = signal.sosfiltfilt(sos, padded)
    if pad:
        filtered = filtered[pad:-pad]
    filtered *= width
    return np.column_stack([mid + filtered, mid - filtered]).astype(np.float32)


def eq_stage(x: Audio, settings: Mapping[str, Any]) -> Audio:
    y = butter(x, 28, "highpass")
    y = shelf(y, 62, 0.7, settings.get("pultec_low_boost_db", 2.2))
    y = bell(y, 285, 1.5, settings.get("mud_cut_db", -2.5))
    y = bell(y, 2700, 1.2, settings.get("mid_bite_db", 1.8))
    y = bell(y, 4800, 2.5, -2.2)
    return shelf(y, 10500, 0.7, settings.get("air_boost_db", 1.6), True)


def parallel_stage(x: Audio, blend: float) -> Audio:
    a = compress(x, -16, 3, 25, 120)
    b = compress(x, -28, 8, 5, 60)
    return np.asarray((1 - blend) * a + blend * b, dtype=np.float32)


def tape(x: Audio, drive: float) -> Audio:
    return np.asarray(
        (np.tanh(drive * x.astype(np.float64) + 0.035) - np.tanh(0.035)) / np.tanh(drive),
        dtype=np.float32,
    )


def loudness(x: Audio) -> float | None:
    if not len(x) or not np.any(x):
        return None
    analysis = np.pad(x, ((0, max(0, 19200 - len(x))), (0, 0)))
    value = float(pyln.Meter(RATE).integrated_loudness(analysis))
    return value if np.isfinite(value) else None


def true_peak(x: Audio) -> float:
    return float(np.max(np.abs(signal.resample_poly(x, 4, 1, axis=0)))) if len(x) else 0.0


def db_peak(peak: float) -> float | None:
    return float(20 * np.log10(peak)) if peak > 0 else None


def measure(x: Audio) -> dict[str, Any]:
    lufs = loudness(x)
    return dict(
        integrated_lufs=lufs,
        sample_peak_dbfs=db_peak(float(np.max(abs(x))) if len(x) else 0),
        true_peak_dbtp=db_peak(true_peak(x)),
        loudness_status="measured" if lufs is not None else "unmeasurable",
    )


def limit(x: Audio) -> Audio:
    # 4x linked detection, symmetric 5ms lookahead/hold; release is 45ms.
    if true_peak(x) <= 10 ** (-0.35 / 20):
        return x.copy()
    up = signal.resample_poly(x, 4, 1, axis=0)
    peak = np.max(abs(up), axis=1)
    future = ndimage.maximum_filter1d(peak, size=1921, mode="nearest")
    target = np.minimum(1, 10 ** (-0.35 / 20) / np.maximum(future, 1e-15))
    alpha = np.exp(-1 / (0.045 * RATE * 4))
    recovery, _ = signal.lfilter([1 - alpha], [1, -alpha], target, zi=[alpha * target[0]])
    gains = np.minimum(target, recovery)
    result = np.asarray(
        signal.resample_poly(up * gains[:, None], 1, 4, axis=0)[: len(x)], dtype=np.float32
    )
    peak_out = true_peak(result)
    if peak_out > 10 ** (-0.35 / 20):
        result *= 10 ** (-0.35 / 20) / peak_out
    return result


@dataclass
class MasterResult:
    audio: Audio
    telemetry: dict[str, Any]
    target_lufs: float


def bypass(x: Audio) -> Audio:
    return x.copy()


def master(audio: Audio, settings: Mapping[str, Any]) -> MasterResult:
    validate_audio(audio)
    width = bounded(settings.get("stereo_width", 1.15), 0, 1.5, "stereo_width")
    blend = bounded(settings.get("parallel_comp_mix", 0.18), 0, 1, "parallel_comp_mix")
    drive = bounded(settings.get("tape_drive", 1.22), 1, 2, "tape_drive")
    target = bounded(settings.get("target_lufs", -9.5), -14, -8, "target_lufs")
    if target not in (-14, -9.5, -8) or settings.get("ceiling_db", -0.3) != -0.3:
        raise DSPError("invalid_master_settings")
    if settings.get("mono_bass_cutoff_hz", 85) != 85:
        raise DSPError("invalid_master_settings")
    for key in ["pultec_low_boost_db", "mud_cut_db", "mid_bite_db", "air_boost_db"]:
        if key in settings:
            bounded(settings[key], -12, 12, key)
    before = measure(audio)
    y = tape(parallel_stage(eq_stage(ms_stage(audio, width), settings), blend), drive)
    level = loudness(y)
    gain_db = 0.0
    if level is not None:
        gain_db = target - level
        y = np.asarray(y * 10 ** (gain_db / 20), dtype=np.float32)
    peak_before_limit = true_peak(y)
    y = limit(y) if len(y) else y
    validate_audio(y)
    after = measure(y)
    if level is not None and abs(after["integrated_lufs"] - target) > 0.2:
        raise DSPError("loudness_target_unreachable")
    metadata = dict(
        before=before,
        after=after,
        target_lufs=target,
        normalization_gain_db=gain_db,
        sample_count=len(y),
        sample_rate=RATE,
        analysis_padded=0 < len(y) < 19200,
        dither_seed=0,
        limiter_reduction_db=max(
            0.0, 20 * np.log10(max(peak_before_limit, 1e-30) / max(true_peak(y), 1e-30))
        ),
        analysis_policy="zero-pad to 400ms for short-file analysis",
        dsp_version="1.0.0",
        versions={
            name: version(name)
            for name in ("numpy", "scipy", "soundfile", "pedalboard", "pyloudnorm")
        },
    )
    return MasterResult(y, metadata, target)


def export_wav(result: MasterResult, path: Path, bit_depth: int = 24) -> Path:
    if bit_depth not in (16, 24):
        raise DSPError("invalid_master_settings", "bit_depth")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(suffix=".wav", dir=path.parent)
    os.close(fd)
    tmp = Path(temp)
    try:
        x = result.audio.astype(np.float64)
        if bit_depth == 16 and np.any(x):
            rng = np.random.default_rng(0)
            x += (rng.uniform(-0.5, 0.5, x.shape) + rng.uniform(-0.5, 0.5, x.shape)) / 32768
        sf.write(tmp, x, RATE, subtype=f"PCM_{bit_depth}")
        decoded, _ = sf.read(tmp, dtype="float32", always_2d=True)
        stats = measure(decoded)
        level = stats["integrated_lufs"]
        peak = stats["true_peak_dbtp"]
        if (level is not None and abs(level - result.target_lufs) > 0.2) or (
            peak is not None and peak > -0.3
        ):
            raise DSPError("loudness_target_unreachable")
        result.telemetry.update(after=stats, bit_depth=bit_depth)
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return path
