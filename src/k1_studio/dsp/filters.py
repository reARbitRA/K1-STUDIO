# SPEC-001 SPEC-002 SPEC-003
"""Fresh, render-local filter state. Native coefficients retain float64 precision."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from pedalboard import (  # type: ignore[attr-defined]
    Compressor,
    Gain,
    PeakFilter,
    Pedalboard,
)
from scipy import signal

Audio = NDArray[np.float32]
RATE = 48000


def butter(x: Audio, hz: float, kind: str, order: int = 2) -> Audio:
    if not len(x):
        return x.copy()
    sos = signal.butter(order, hz, btype=kind, fs=RATE, output="sos")
    return np.asarray(signal.sosfilt(sos, x, axis=0), dtype=np.float32)


def gain(x: Audio, db: float) -> Audio:
    if not len(x):
        return x.copy()
    return np.asarray(Pedalboard([Gain(gain_db=db)])(x.T.copy(), RATE).T, dtype=np.float32)


def bell(x: Audio, hz: float, q: float, db: float) -> Audio:
    if not len(x) or db == 0:
        return x.copy()
    return np.asarray(
        Pedalboard([PeakFilter(cutoff_frequency_hz=hz, q=q, gain_db=db)])(x.T.copy(), RATE).T,
        dtype=np.float32,
    )


def shelf(x: Audio, hz: float, q: float, db: float, high: bool = False) -> Audio:
    # RBJ shelf, with alpha=sin(w0)/(2Q); no hidden compensation.
    a = 10 ** (db / 40)
    w = 2 * np.pi * hz / RATE
    c = np.cos(w)
    s = np.sin(w)
    alpha = s / (2 * q)
    z = 2 * np.sqrt(a) * alpha
    if high:
        b = [
            a * ((a + 1) + (a - 1) * c + z),
            -2 * a * ((a - 1) + (a + 1) * c),
            a * ((a + 1) + (a - 1) * c - z),
        ]
        den = [(a + 1) - (a - 1) * c + z, 2 * ((a - 1) - (a + 1) * c), (a + 1) - (a - 1) * c - z]
    else:
        b = [
            a * ((a + 1) - (a - 1) * c + z),
            2 * a * ((a - 1) - (a + 1) * c),
            a * ((a + 1) - (a - 1) * c - z),
        ]
        den = [(a + 1) + (a - 1) * c + z, -2 * ((a - 1) + (a + 1) * c), (a + 1) + (a - 1) * c - z]
    return np.asarray(signal.lfilter(b, den, x, axis=0), dtype=np.float32)


def compress(x: Audio, threshold: float, ratio: float, attack: float, release: float) -> Audio:
    if not len(x) or ratio == 1:
        return x.copy()
    processor = Compressor(
        threshold_db=threshold, ratio=ratio, attack_ms=attack, release_ms=release
    )
    return np.asarray(Pedalboard([processor])(x.T.copy(), RATE).T, dtype=np.float32)
