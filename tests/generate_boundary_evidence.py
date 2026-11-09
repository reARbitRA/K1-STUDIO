"""Reproducible synthetic AC-10 fixtures; no human listening verdict is automated."""

from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

from k1_studio.dsp.regions import apply_regions


def main() -> None:
    out = Path(".verification/boundaries")
    out.mkdir(parents=True, exist_ok=True)
    for hz in (55, 110, 220):
        mono = 10 ** (-3 / 20) * np.sin(np.arange(96000) * 2 * np.pi * hz / 48000)
        audio = np.column_stack([mono, mono]).astype(np.float32)
        for preset in ("HARD_MUTE", "NASA_WALKIE_TALKIE"):
            result = apply_regions(
                audio,
                [
                    dict(
                        region_id="evidence",
                        start_sec=0.5,
                        end_sec=1.5,
                        effect_type=preset,
                        wet_mix=1,
                        fade_ms=8,
                    )
                ],
            )
            stem = out / f"{hz}-{preset}"
            sf.write(stem.with_suffix(".wav"), result.audio, 48000, subtype="FLOAT")
            freq, t, spectrum = signal.spectrogram(result.audio[:, 0], 48000, nperseg=512)
            np.savez_compressed(
                stem.with_suffix(".npz"),
                frequency_hz=freq,
                time_sec=t,
                power=spectrum,
                audio=result.audio,
                boundaries=result.boundaries,
            )
            # Inspectable vector spectrogram, ≤5kHz. Data/artifacts stay out of Git.
            db = 10 * np.log10(np.maximum(spectrum, 1e-14))
            rows = freq <= 5000
            matrix = db[rows, ::2]
            rects = []
            for y, row in enumerate(matrix):
                for x, value in enumerate(row):
                    level = int(np.clip((value + 100) / 80, 0, 1) * 255)
                    rects.append(
                        f'<rect x="{x * 2}" y="{(len(matrix) - y) * 4}" width="2" '
                        f'height="4" fill="rgb({level // 4},{level},{min(255, level + 20)})"/>'
                    )
            svg = (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{matrix.shape[1] * 2}" '
                f'height="{len(matrix) * 4 + 20}" style="background:#0d0e12">'
                f"<title>{hz} Hz / {preset}; time 0–2s, frequency 0–5kHz</title>"
                + "".join(rects)
                + "</svg>"
            )
            stem.with_suffix(".svg").write_text(svg)
    print(f"Generated six WAV + spectrogram/data sets in {out}; listening sign-off pending.")


if __name__ == "__main__":
    main()
