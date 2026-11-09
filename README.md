<div align="center">

<!-- Animated Audio Wave Header SVG -->
<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&color=0:0D0E12,50:16181F,100:E11D48&height=220&section=header&text=K1-STUDIO&fontSize=68&fontColor=FFFFFF&fontAlignY=38&desc=32-Bit%20Float%20Surgical%20Stem-Mixing%20%26%20Analog%20Mastering%20Workstation&descSize=18&descColor=06B6D4&descAlignY=62&animation=fadeIn" alt="K1-STUDIO Banner" />

<!-- Animated Terminal DSP Ticker SVG -->
<a href="https://github.com/reARbitRA/K1-STUDIO">
  <img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=600&size=15&duration=2800&pause=900&color=E11D48&background=0D0E1200&center=true&vCenter=true&width=820&lines=48+kHz+%2F+32-Bit+IEEE+Float+Zero-Latency+DSP+Engine;Click-Free+Zero-Crossing+Surgical+Region+Automation;Zero-Phase+Sub-85Hz+Mid%2FSide+Mono+Matrix+%2B+Pultec+EQP-1A+Curve;Parallel+SSL+G-Bus+Glue+%2B+1176+FET+Crush+%2B+Studer+A800+Tape+Saturation;ITU-R+BS.1770-4+LUFS+Loudness+Normalization+%26+-0.3+dBTP+True-Peak+Limiting" alt="DSP Pipeline Ticker" />
</a>

<br/>

<!-- Studio Tech Badges -->
![DSP Engine](https://img.shields.io/badge/DSP_CORE-32--BIT_FLOAT_%2F_48kHz-E11D48?style=for-the-badge&logo=audacity&logoColor=white)
![Backend](https://img.shields.io/badge/BACKEND-Python_3.11_%7C_FastAPI_%7C_Pedalboard-06B6D4?style=for-the-badge&logo=python&logoColor=white)
![Frontend](https://img.shields.io/badge/STUDIO_UI-React_18_%7C_TypeScript_%7C_WaveSurfer_v7-16181F?style=for-the-badge&logo=react&logoColor=06B6D4)
![Output](https://img.shields.io/badge/MASTER_EXPORT-24--BIT_PCM_WAV-10B981?style=for-the-badge)

</div>

---

## Overview

**K1-STUDIO** is a local-first, single-screen Digital Audio Workstation (DAW) and mastering console engineered for surgical post-production, stem mixing, non-destructive time-region FX automation, and analog-modeled mastering.

Unlike traditional bloated DAWs that require tedious sample-level slicing and manual crossfade drawing, **K1-STUDIO** uses a deterministic **Zero-Crossing Region DSP Engine**: select any time interval on the waveform, assign an effect preset, and the engine automatically locates the nearest zero-crossing within `±5 ms` and applies raised-cosine micro-crossfades for 100% click-free transitions.

---

## Signal Processing Architecture

```mermaid
flowchart LR
    subgraph INGEST["1. Ingest & Stem Engine"]
        A["WAV / FLAC / AIFF"] --> B["48kHz / Float32 Resampler"]
        B --> C["Optional Demucs v4\n2-Stem / 4-Stem Split"]
    end

    subgraph TRACK["2. Per-Track Channel Strip"]
        C --> D["Pre-Gain & Phase Ø"]
        D --> E["HPF + De-Mud (290Hz)\nPresence (2.65kHz) + De-Fizz"]
        E --> F["Channel Compressor"]
        F --> G["Zero-Crossing Region FX\n(Raised-Cosine Crossfade)"]
        G --> H["-3dB Equal-Power Pan"]
    end

    subgraph MASTER["3. Analog Master Bus"]
        H --> I["-6dBFS Summing Headroom"]
        I --> J["Mid/Side Matrix\nZero-Phase <85Hz Mono"]
        J --> K["Pultec EQP-1A Curve"]
        K --> L["Parallel Bus Comp\n82% SSL Glue + 18% 1176"]
        L --> M["Studer A800 Asymmetric\nTanh Tape Saturation"]
        M --> N["BS.1770-4 LUFS Normalizer\n& -0.3 dBTP Brickwall Limiter"]
        N --> O["Verified 24-Bit PCM WAV"]
    end

    style INGEST fill:#12131A,stroke:#06B6D4,stroke-width:1px,color:#fff
    style TRACK fill:#12131A,stroke:#E11D48,stroke-width:1px,color:#fff
    style MASTER fill:#12131A,stroke:#10B981,stroke-width:1px,color:#fff
