# SPEC-002
from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy import signal

from .engine import DSPError
from .filters import RATE, Audio, bell, butter, compress, gain

PRESETS = (
    "HARD_MUTE",
    "NASA_WALKIE_TALKIE",
    "UNDERWATER_WOMB",
    "ANALOG_TAPE_STOP",
    "TAPE_STUTTER_DEGRADE",
    "SUB_40HZ_DROP",
)


def tape_positions(n: int) -> tuple[NDArray[Any], NDArray[Any]]:
    u = np.linspace(0, 1, n)
    speed = np.maximum(0.02, (1 - u) ** 1.8)
    positions = np.concatenate(([0.0], np.cumsum(speed[:-1])))[:n]
    return positions, speed


def interpolate(x: Audio, positions: NDArray[Any]) -> Audio:
    return np.column_stack(
        [np.interp(positions, np.arange(len(x)), x[:, c]) for c in range(2)]
    ).astype(np.float32)


def process(x: Audio, effect: str, bpm: float | None = None) -> Audio:
    n = len(x)
    if effect not in PRESETS:
        raise DSPError("unknown_effect", "effect_type")
    if not n:
        return x.copy()
    if effect == "HARD_MUTE":
        return np.zeros_like(x)
    if effect == "NASA_WALKIE_TALKIE":
        y = bell(butter(butter(x, 520, "highpass"), 2400, "lowpass"), 1350, 2, 3.5)
        y = np.tanh(y * 10 ** (14 / 20)).astype(np.float32)
        return gain(compress(y, -28, 10, 1, 40), -7.5)
    if effect == "UNDERWATER_WOMB":
        return bell(butter(x, 310, "lowpass", 4), 270, 1.8, 4)
    if effect == "ANALOG_TAPE_STOP":
        positions, _ = tape_positions(n)
        y = interpolate(x, positions)
        fade = min(n, 240)
        weights = 0.5 * (1 + np.cos(np.linspace(0, np.pi, fade)))
        y[-fade:] *= weights[:, None]
        return y
    u = np.linspace(0, 1, n)
    if effect == "SUB_40HZ_DROP":
        freq = 90 * (36 / 90) ** u
        phase = 2 * np.pi * np.concatenate(([0.0], np.cumsum(freq[:-1]))) / RATE
        sub = (10 ** (-6 / 20) * np.exp(-6 * u) * np.sin(phase)).astype(np.float32)
        return np.asarray(x + sub[:, None], dtype=np.float32)
    length = max(2, min(n, round((60 / bpm if bpm else 0.25) * RATE)))
    t = np.arange(n) / RATE
    cents = u * (15 * np.sin(2 * np.pi * 0.6 * t) + 5 * np.sin(2 * np.pi * 6 * t))
    positions = np.concatenate(([0.0], np.cumsum(2 ** (cents[:-1] / 1200)))) % length
    loop = x[:length].copy()
    seam = min(144, length // 2)
    if seam > 1:
        w = 0.5 * (1 - np.cos(np.linspace(0, np.pi, seam)))
        loop[-seam:] = loop[-seam:] * (1 - w[:, None]) + loop[:seam] * w[:, None]
    y = interpolate(loop, positions)
    result = np.empty_like(y)
    state = np.zeros((1, 2, 2))
    for start in range(0, n, 48):
        cutoff = 600.0 if start + 48 >= n else 8000 * (600 / 8000) ** u[start]
        sos = signal.butter(2, cutoff, fs=RATE, output="sos")
        block, state = signal.sosfilt(sos, y[start : start + 48], axis=0, zi=state)
        result[start : start + 48] = block
    return result
