# SPEC-001
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from math import gcd
from typing import Any

import numpy as np
from scipy import signal

from .filters import RATE, Audio, bell, butter, compress, gain


class DSPError(ValueError):
    def __init__(self, code: str, field: str | None = None):
        self.code, self.field = code, field
        super().__init__(code)


def bounded(value: Any, low: float, high: float, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise DSPError("invalid_parameter", field)
    if not np.isfinite(value) or not low <= value <= high:
        raise DSPError("invalid_parameter", field)
    return float(value)


def validate_audio(x: Audio) -> None:
    if x.ndim != 2 or x.shape[1] != 2 or not np.isfinite(x).all():
        raise DSPError("invalid_audio")


def canonicalize(audio: Audio, input_sample_rate: int) -> Audio:
    if type(input_sample_rate) is not int or input_sample_rate <= 0:
        raise DSPError("invalid_audio", "sample_rate")
    x = np.asarray(audio)
    if x.ndim != 2 or x.shape[1] not in (1, 2):
        raise DSPError("unsupported_audio")
    if not np.isfinite(x).all():
        raise DSPError("invalid_audio")
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    if input_sample_rate != RATE and len(x):
        divisor = gcd(RATE, input_sample_rate)
        x = signal.resample_poly(x, RATE // divisor, input_sample_rate // divisor, axis=0)
    result = np.asarray(x, dtype=np.float32).copy()
    validate_audio(result)
    return result


def gain_phase(x: Audio, db: float, invert: bool) -> Audio:
    validate_audio(x)
    bounded(db, -24, 12, "gain_db")
    if type(invert) is not bool:
        raise DSPError("invalid_parameter", "phase_invert")
    return np.asarray(gain(x, db) * (-1 if invert else 1), dtype=np.float32)


def pan(x: Audio, p: float) -> Audio:
    p = bounded(p, -1, 1, "pan")
    theta = (p + 1) * np.pi / 4
    return np.asarray(x * np.array([np.cos(theta), np.sin(theta)]), dtype=np.float32)


STRIP = {
    "hp_hz": (20, 500, 20),
    "de_mud_db": (-6, 3, -2),
    "presence_db": (-6, 6, 0),
    "de_fizz_db": (-6, 0, -1.8),
    "comp_threshold_db": (-40, 0, -18),
    "comp_ratio": (1, 10, 4),
    "comp_attack_ms": (1, 100, 25),
    "comp_release_ms": (20, 500, 120),
}


def channel_strip(x: Audio, settings: Mapping[str, Any]) -> Audio:
    values = {
        k: bounded(settings.get(k, default), low, high, k)
        for k, (low, high, default) in STRIP.items()
    }
    y = butter(x, values["hp_hz"], "highpass")
    for hz, q, key in [
        (290, 1.6, "de_mud_db"),
        (2650, 1.2, "presence_db"),
        (4850, 2.5, "de_fizz_db"),
    ]:
        y = bell(y, hz, q, values[key])
    return compress(
        y,
        values["comp_threshold_db"],
        values["comp_ratio"],
        values["comp_attack_ms"],
        values["comp_release_ms"],
    )


def render_track(
    audio: Audio,
    settings: Mapping[str, Any],
    region_processor: Callable[[Audio, Any], Audio] | None = None,
) -> Audio:
    y = gain_phase(audio, settings.get("gain_db", 0), settings.get("phase_invert", False))
    y = channel_strip(y, settings.get("channel_strip", {}))
    if region_processor:
        y = region_processor(y, settings.get("regions", []))
    return pan(y, settings.get("pan", 0))


@dataclass
class MixResult:
    audio: Audio
    pre_master_gain_db: float


def mix_tracks(buffers: Sequence[Audio], settings: Sequence[Mapping[str, Any]]) -> MixResult:
    if len(buffers) != len(settings):
        raise DSPError("invalid_parameter", "tracks")
    for item in settings:
        if any(type(item.get(flag, False)) is not bool for flag in ("mute", "solo")):
            raise DSPError("invalid_parameter", "mute/solo")
    n = max((len(b) for b in buffers), default=0)
    output = np.zeros((n, 2), dtype=np.float64)
    any_solo = any(s.get("solo", False) for s in settings)
    for x, s in zip(buffers, settings, strict=True):
        validate_audio(x)
        if not s.get("mute", False) and (not any_solo or s.get("solo", False)):
            output[: len(x)] += x
    peak = float(np.max(np.abs(output))) if n else 0
    scale = 10 ** (-6 / 20) / max(1, peak)
    return MixResult(np.asarray(output * scale, dtype=np.float32), float(20 * np.log10(scale)))
