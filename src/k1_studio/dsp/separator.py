# SPEC-004
"""No model download is performed. Explicit local model repository is required."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np

from .engine import DSPError, canonicalize
from .filters import Audio


def separate(audio: Audio, mode: str) -> dict[str, Audio]:
    repo = os.environ.get("K1_DEMUCS_MODELS")
    if not repo or not Path(repo).is_dir():
        raise DSPError("model_unavailable")
    try:
        import torch
        from demucs.apply import apply_model
        from demucs.pretrained import get_model

        model = get_model("htdemucs" if mode == "2stem" else "htdemucs_ft", repo=Path(repo))
        model.eval()
        from scipy import signal

        x = signal.resample_poly(audio, model.samplerate, 48000, axis=0).astype(np.float32)
        with torch.no_grad():
            output = apply_model(model, torch.from_numpy(x.T)[None], device="cpu", shifts=0)[0]
        names = {"vocals": "Vocals", "drums": "Drums", "bass": "Bass", "other": "Other"}
        return {
            names[name]: canonicalize(output[i].cpu().numpy().T, model.samplerate)
            for i, name in enumerate(model.sources)
        }
    except (ImportError, RuntimeError, FileNotFoundError, KeyError) as exc:
        raise DSPError("model_unavailable") from exc
