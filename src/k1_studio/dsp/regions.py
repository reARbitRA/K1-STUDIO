# SPEC-002
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .engine import DSPError, bounded, validate_audio
from .filters import RATE, Audio
from .presets import PRESETS, process


def snap(audio: Audio, index: int) -> int:
    mid = audio.mean(axis=1)
    lo = max(0, index - 240)
    hi = min(len(mid), index + 241)
    candidates = []
    for n in range(lo, hi):
        if mid[n] == 0 or (n + 1 < len(mid) and np.sign(mid[n]) != np.sign(mid[n + 1])):
            candidates.append(n)
    return min(candidates, key=lambda n: (abs(n - index), n)) if candidates else index


def envelope(n: int, fade: int) -> NDArray[Any]:
    f = min(fade, n // 2)
    w = np.ones(n, dtype=np.float32)
    if f:
        edge = 0.5 * (1 - np.cos(np.linspace(0, np.pi, f))) if f > 1 else np.zeros(1)
        w[:f] = edge
        w[-f:] = edge[::-1]
    return w


@dataclass
class RegionResult:
    audio: Audio
    boundaries: list[dict[str, Any]]


def apply_regions(
    audio: Audio,
    regions: Sequence[Mapping[str, Any]],
    sample_rate: int = RATE,
    bpm: float | None = None,
) -> RegionResult:
    validate_audio(audio)
    if sample_rate != RATE:
        raise DSPError("invalid_region", "sample_rate")
    if bpm is not None:
        bounded(bpm, 1e-6, 10000, "bpm")
    validated = []
    for reg in regions:
        try:
            start = bounded(reg["start_sec"], 0, len(audio) / RATE, "start_sec")
            end = bounded(reg["end_sec"], 0, len(audio) / RATE, "end_sec")
            wet = bounded(reg.get("wet_mix", 1), 0, 1, "wet_mix")
            fade = bounded(reg.get("fade_ms", 8), 2, 15, "fade_ms")
            a, b = int(np.floor(start * RATE + 0.5)), int(np.floor(end * RATE + 0.5))
            if b - a < 2:
                raise DSPError("invalid_region")
        except (KeyError, DSPError) as exc:
            raise DSPError("invalid_region") from exc
        effect = reg.get("effect_type")
        if effect not in PRESETS:
            raise DSPError("unknown_effect", "effect_type")
        validated.append((a, b, wet, 3 if effect == "HARD_MUTE" else fade, effect))
    output = audio.copy()
    bounds = []
    for a, b, wet, fade, effect in validated:
        s0, s1 = snap(output, a), snap(output, b)
        if s1 - s0 < 2:
            s0, s1 = a, b
        f = min(int(np.floor(fade * 48 + 0.5)), (s1 - s0) // 2)
        dry = output[s0:s1].copy()
        if wet:
            fx = process(dry, effect, bpm)
            w = envelope(len(dry), f)[:, None] * wet
            output[s0:s1] = dry + w * (fx - dry)
        bounds.append(
            dict(
                requested_start=a,
                requested_end=b,
                start=s0,
                end=s1,
                fade_samples=f,
                effect_type=effect,
                preset_version=1,
            )
        )
    return RegionResult(output, bounds)
