TECHNICAL SPECIFICATION & ARCHITECTURE DOCUMENT
Project Name: K1-STUDIO — Personal Surgical Stem-Mixing, Region-DSP & Analog Mastering DAW
1. Executive Summary & Product Vision
K1-STUDIO is a lightweight, high-precision, local-first Digital Audio Workstation (DAW) engineered specifically for post-producing, surgically editing, mixing, and mastering AI-generated music (Suno, ACE-Step) and multi-track stems.

Traditional DAWs (Ableton, Cubase, Logic) suffer from UI bloat and require hundreds of manual micro-edits (scissors, crossfade handles, complex routing) for simple tasks. K1-STUDIO replaces manual timeline surgery with a Non-Destructive Region-Based DSP Engine and a 32-Bit Float Analog Mastering Pipeline, controlled through a low-friction, high-contrast web interface.

2. Core UX & Ergonomic Principles
Zero Manual Micro-Slicing: Users never have to manually zoom into sample-level waveforms to draw crossfades or cut clips. Selecting a time region on the waveform and assigning a tag (e.g., Hard Mute, NASA Radio, Underwater, Tape Stop) automatically computes zero-crossing points and applies click-free raised-cosine micro-fades in the backend.
Low-Friction Input Design: Every operation must be achievable with minimal pointer travel—single-click region presets, macro rotary knobs, and numeric start/end timestamp inputs.
AI-Artifact Remediation by Default: Built-in spectral and dynamic processors specifically tuned to eliminate common generative-AI audio flaws (250–350Hz boxy mud, 4.5–6kHz digital fizz/whistling, and stereo sub-bass phase smear).
3. System Architecture & Technology Stack
text

+-----------------------------------------------------------------------------------+
| FRONTEND (SPA - React 18 + TypeScript + Vite + TailwindCSS)                       |
|  - Timeline & Waveform Engine: WaveSurfer.js v7 (Regions, Timeline, Minimap)      |
|  - State Management: Zustand (Immutable JSON Project Graph + Undo/Redo Stack)     |
|  - Real-time Preview: Web Audio API (Transport Sync, Solo/Mute, Level Meters)     |
+-----------------------------------------+-----------------------------------------+
                                          | REST API (FastAPI) + WebSocket (Progress)
                                          v
+-----------------------------------------------------------------------------------+
| BACKEND CONTROLLER (Python 3.11+ / FastAPI / Uvicorn / AsyncIO)                   |
|  - Session Manager, Non-Destructive Edit Decision List (EDL), Preset Store        |
|  - Stem Separation Worker: Demucs v4 (`htdemucs` 2-stem & `htdemucs_ft` 4-stem)   |
+-----------------------------------------+-----------------------------------------+
                                          | 32-Bit IEEE Float PCM Buffers (48kHz)
                                          v
+-----------------------------------------------------------------------------------+
| CORE DSP ENGINE (C++ Bound via Spotify Pedalboard + SciPy + NumPy + PyLoudnorm)   |
|  1. Track Node: Pre-Gain -> Phase Invert -> Channel Strip EQ/Comp -> Region DSP   |
|                 (Zero-Crossing + Cosine Crossfade) -> -3dB Equal-Power Pan        |
|  2. Summing Bus: 32-Bit Float Headroom Normalization (-6dBFS pre-master)          |
|  3. Master Bus: Mid/Side Matrix (Zero-Phase Sub-85Hz Mono + Width) -> Pultec EQ   |
|                 -> Parallel Bus Comp (SSL Glue + 1176 Crush) -> Asymmetric Tanh   |
|                 Studer A800 Tape Saturation -> ITU-R BS.1770-4 LUFS Normalizer    |
|                 -> True-Peak Ceiling Limiter (-0.3 dBTP) -> 24-Bit WAV Export     |
+-----------------------------------------------------------------------------------+
3.1 Tech Stack Requirements
Backend: Python 3.11+, fastapi, uvicorn, pedalboard (Spotify C++/JUCE wrapper), numpy, scipy, soundfile (libsndfile), pyloudnorm, demucs (or audio-separator with ONNX/PyTorch acceleration).
Frontend: React 18+, TypeScript, Vite, TailwindCSS (Dark Studio Theme), wavesurfer.js (v7+), lucide-react (icons), zustand.
4. Detailed DSP Pipeline Specifications
All internal audio buffers must be resampled upon ingestion to 48,000 Hz and represented as 32-bit floating-point (float32) NumPy arrays of shape (N, 2) for stereo interleaved operations.

4.1 Module A: Local AI Stem Separation Node
When the user uploads a single stereo master file, the system offers three ingestion modes:

Direct Stereo Track: No separation; loads directly onto Track 1.
2-Stem Split (Phase-Pure Mode): Runs htdemucs isolating Vocals and Instrumental (by summing Drums + Bass + Other internally before output to maintain 100% phase coherence).
4-Stem Split (Full Mix Mode): Runs htdemucs_ft isolating Vocals, Drums, Bass, and Other/Synths.
4.2 Module B: Per-Track Channel Strip
Each track exposes a tailored Channel Strip executed via pedalboard.Pedalboard:

Input Gain: -24.0 dB to +12.0 dB
Polarity (Phase) Invert: 
x
[
n
]
=
−
x
[
n
]
x[n]=−x[n]
High-Pass Filter: 20 Hz to 500 Hz (12 dB/oct)
AI De-Mud Filter (Bell): Center 290 Hz, Q 1.6, Gain -6.0 dB to +3.0 dB
Presence / Punk Bite Filter (Bell): Center 2650 Hz, Q 1.2, Gain -6.0 dB to +6.0 dB
AI De-Fizz Filter (High-Mid Notch/Bell): Center 4850 Hz, Q 2.5, Gain -6.0 dB to 0.0 dB
Channel Compressor: Threshold (-40 to 0 dB), Ratio (1:1 to 10:1), Attack (1 to 100 ms), Release (20 to 500 ms).
Equal-Power Stereo Panning Law (-3 dB Center):
Given pan parameter 
p
∈
[
−
1.0
,
+
1.0
]
p∈[−1.0,+1.0], map to angle 
θ
=
(
p
+
1.0
)
π
4
θ=(p+1.0) 
4
π
​
 :
G
L
=
cos
⁡
(
θ
)
,
G
R
=
sin
⁡
(
θ
)
G 
L
​
 =cos(θ),G 
R
​
 =sin(θ)
4.3 Module C: Click-Free Surgical Region Automation Engine
Users can define any number of time-bounded regions 
R
i
=
[
t
start
,
t
end
]
R 
i
​
 =[t 
start
​
 ,t 
end
​
 ] on any track (or on the Master Bus) and assign an effect preset.

Zero-Crossing & Raised-Cosine Crossfade Algorithm:
To guarantee zero clicks/pops at region boundaries:

Convert 
t
start
t 
start
​
  and 
t
end
t 
end
​
  to sample indices 
s
0
,
s
1
s 
0
​
 ,s 
1
​
 .
Search within a 
±
5
 ms
±5 ms window (
±
240
±240 samples at 48kHz) around 
s
0
s 
0
​
  and 
s
1
s 
1
​
  for the nearest zero-crossing where 
sign
(
x
[
n
]
)
≠
sign
(
x
[
n
+
1
]
)
sign(x[n])

=sign(x[n+1]).
Compute the processed audio buffer 
y
[
s
0
:
s
1
]
=
FX
(
x
[
s
0
:
s
1
]
)
y[s 
0
​
 :s 
1
​
 ]=FX(x[s 
0
​
 :s 
1
​
 ]).
Apply a symmetric Raised-Cosine (Hann) Micro-Crossfade of length 
L
fade
∈
[
2
 ms
,
15
 ms
]
L 
fade
​
 ∈[2 ms,15 ms] at both boundaries:
w
in
[
k
]
=
0.5
(
1
−
cos
⁡
(
π
k
L
fade
)
)
,
w
out
[
k
]
=
1.0
−
w
in
[
k
]
w 
in
​
 [k]=0.5(1−cos( 
L 
fade
​
 
πk
​
 )),w 
out
​
 [k]=1.0−w 
in
​
 [k]
Required Built-in Region FX Presets:
HARD_MUTE (True Zero-Crossing Silence):
Zeros all samples 
y
[
n
]
=
0.0
y[n]=0.0 within the region with a 3 ms raised-cosine boundary fade. Used for razor-sharp stop-start punk/industrial breaks.
NASA_WALKIE_TALKIE (2kHz Bandpass Radio Transmission):
High-Pass Filter at 520 Hz + Low-Pass Filter at 2400 Hz
Resonant Peak at 1350 Hz (+3.5 dB, Q 2.0)
Soft-Clipping Overdrive (+14 dB drive)
Heavy FET Compression (Threshold -28 dB, Ratio 10:1, Attack 1 ms, Release 40 ms)
Output trim -7.5 dB
UNDERWATER_WOMB (300Hz Claustrophobic LPF):
4th-order Low-Pass Filter at 310 Hz
Resonant Bump at 270 Hz (+4.0 dB, Q 1.8)
ANALOG_TAPE_STOP (Decelerating Pitch/Time Brake):
Resamples the region along a non-linear deceleration curve 
v
(
t
)
=
(
1
−
t
)
γ
v(t)=(1−t) 
γ
  (
γ
=
1.8
γ=1.8) from normal speed (
1.0
×
1.0×) down to 
0.02
×
0.02×, followed by a 5 ms fade-out.
TAPE_STUTTER_DEGRADE (Looping Cassette Decay):
Slices the first 250 ms (or 1 beat) of the region and repeats it across the region duration while progressively lowering the Low-Pass cutoff from 8 kHz to 600 Hz and increasing wow/flutter pitch drift.
SUB_40HZ_DROP (Cinematic Sub-Bass Impact):
Synthesizes a phase-locked sine sweep from 90 Hz down to 36 Hz with exponential amplitude decay and mixes it at -6 dBFS underneath the region.
4.4 Module D: Analog Master Bus Pipeline
After summing all active tracks with a -6.0 dBFS pre-master headroom safety scaling, the Master Bus executes the following 5 stages in strict order:

Mid/Side Matrix & Sub-Bass Mono Maker:
Encode: 
M
=
0.5
(
L
+
R
)
M=0.5(L+R), 
S
=
0.5
(
L
−
R
)
S=0.5(L−R)
Apply a Zero-Phase 4th-Order Butterworth High-Pass Filter (scipy.signal.sosfiltfilt) at 85 Hz exclusively to the Side (
S
S) channel. This forces all sub-bass energy below 85 Hz into 100% phase-coherent center mono.
Multiply Side channel by stereo_width parameter (
∈
[
0.0
,
1.5
]
∈[0.0,1.5], default 1.15).
Decode: 
L
′
=
M
+
S
′
L 
′
 =M+S 
′
 , 
R
′
=
M
−
S
′
R 
′
 =M−S 
′
 .
Master Surgical & Pultec-Style EQ:
Sub-rumble High-Pass: 28 Hz
Pultec Low-End Shelf Boost: 62 Hz (+2.2 dB, Q 0.7)
Low-Mid Mud Cut: 285 Hz (-2.5 dB, Q 1.5)
Upper-Mid Attack/Vocal Presence: 2700 Hz (+1.8 dB, Q 1.2)
Harshness/AI Whistle Cut: 4800 Hz (-2.2 dB, Q 2.5)
Analog Air High-Shelf: 10,500 Hz (+1.6 dB, Q 0.7)
Parallel Console Bus Compression (SSL Glue + 1176 Crush):
Path A (Glue - 82% blend): Threshold -16 dB, Ratio 3:1, Attack 25 ms, Release 120 ms.
Path B (Crush - 18% blend): Threshold -28 dB, Ratio 8:1, Attack 5 ms, Release 60 ms.
Studer A800 2-Inch Analog Tape Saturation:
Asymmetric hyperbolic tangent transfer function generating both even and odd harmonics:
y
[
n
]
=
tanh
⁡
(
d
⋅
x
[
n
]
+
α
)
−
tanh
⁡
(
α
)
tanh
⁡
(
d
)
y[n]= 
tanh(d)
tanh(d⋅x[n]+α)−tanh(α)
​
 
where drive 
d
∈
[
1.0
,
2.0
]
d∈[1.0,2.0] (default 1.22) and asymmetry bias 
α
=
0.035
α=0.035.
ITU-R BS.1770-4 Loudness Normalizer & True-Peak Limiter:
Measure integrated loudness via pyloudnorm.Meter(48000).
Normalize gain to target LUFS (user selectable: -14.0 LUFS streaming, -9.5 LUFS industrial/punk club master, -8.0 LUFS aggressive).
Final brickwall Limiter at -0.3 dB ceiling with 45 ms release.
Export as 24-bit PCM WAV (PCM_24) and 16-bit Dithered WAV.
5. API Contract & Data Models (JSON Schemas)
5.1 Project State Schema (POST /api/v1/project/render)
JSON

{
  "project_id": "hich_session_01",
  "sample_rate": 48000,
  "master_bus": {
    "mono_bass_cutoff_hz": 85.0,
    "stereo_width": 1.15,
    "pultec_low_boost_db": 2.2,
    "mud_cut_db": -2.5,
    "mid_bite_db": 1.8,
    "air_boost_db": 1.6,
    "parallel_comp_mix": 0.18,
    "tape_drive": 1.22,
    "target_lufs": -9.5,
    "ceiling_db": -0.3
  },
  "tracks": [
    {
      "track_id": "trk_vocals",
      "name": "Vocals",
      "file_path": "/workspace/stems/vocals.wav",
      "gain_db": 1.5,
      "pan": 0.0,
      "mute": false,
      "solo": false,
      "phase_invert": false,
      "channel_strip": {
        "hp_hz": 75.0,
        "de_mud_db": -2.0,
        "presence_db": 2.5,
        "de_fizz_db": -1.8,
        "comp_threshold_db": -18.0,
        "comp_ratio": 4.0
      },
      "regions": [
        {
          "region_id": "reg_01",
          "start_sec": 4.12,
          "end_sec": 4.88,
          "effect_type": "HARD_MUTE",
          "wet_mix": 1.0,
          "fade_ms": 3.0
        },
        {
          "region_id": "reg_02",
          "start_sec": 165.00,
          "end_sec": 188.50,
          "effect_type": "UNDERWATER_WOMB",
          "wet_mix": 0.85,
          "fade_ms": 10.0
        },
        {
          "region_id": "reg_03",
          "start_sec": 280.00,
          "end_sec": 312.40,
          "effect_type": "NASA_WALKIE_TALKIE",
          "wet_mix": 1.0,
          "fade_ms": 8.0
        }
      ]
    }
  ]
}
5.2 Core Backend Endpoints
POST /api/v1/ingest/upload — Uploads raw audio file, normalizes sample rate to 48kHz, returns waveform peak JSON for instant UI rendering.
POST /api/v1/ingest/split-stems — Triggers async Demucs job (mode: "2stem" | "4stem"), streams progress over WebSocket /ws/jobs/{job_id}, and auto-populates project tracks.
POST /api/v1/preview/region — Renders only a [start_sec - 2.0, end_sec + 2.0] slice with the selected Region FX and Master chain applied, returning a fast WAV stream in < 300ms for instant auditioning.
POST /api/v1/project/render — Executes full 32-bit float mixdown and mastering, returning download URLs and before/after LUFS/Peak telemetry.
6. Frontend UI Layout & Component Specification
The UI must be a single-screen, zero-scroll dark interface (#0D0E12 background, #16181F panels, #E11D48 crimson & #06B6D4 cyan accents) divided into four zones:

text

+-----------------------------------------------------------------------------------+
| TOP BAR: [Import Audio] [Split: 2-Stem | 4-Stem] | [Play/Pause] [Timecode] [LUFS] |
|          [Undo] [Redo]                           | [Preview Region] [EXPORT WAV]  |
+-----------------------------------------------------------------------------------+
| TRACK HEADERS (Left 240px) | MULTI-TRACK WAVEFORM & REGION CANVAS (WaveSurfer v7) |
| -------------------------- | ---------------------------------------------------- |
| [1] VOCALS     [M][S][Ø]   |  ~~~||~~~~| [REG: UNDERWATER] |~~~~| [REG: NASA] |~~ |
| Gain: +1.5dB   Pan: C      |                                                      |
| -------------------------- | ---------------------------------------------------- |
| [2] BASS       [M][S][Ø]   |  █████████| [REG: HARD MUTE]  |█████████████████████ |
| Gain: +0.5dB   Pan: C      |                                                      |
| -------------------------- | ---------------------------------------------------- |
| [3] DRUMS      [M][S][Ø]   |  █████████| [REG: HARD MUTE]  |█████████████████████ |
| Gain:  0.0dB   Pan: C      |                                                      |
+-----------------------------------------------------------------------------------+
| SURGICAL REGION INSPECTOR (Bottom-Left)   | ANALOG MASTERING CONSOLE (Bottom-Right)|
| ----------------------------------------- | ------------------------------------- |
| Selected Region: [ 04.120s ] to [ 04.880s]| [Mono Sub <85Hz] [Stereo Width: 115%] |
| Apply Target: [All Tracks (Master Cut) v] | [Pultec Low] [De-Mud] [Bite] [Air]    |
| One-Tap Preset:                           | [Parallel Crush: 18%] [Tape: 1.22x]   |
| [HARD MUTE] [NASA RADIO] [UNDERWATER]     | [Target Loudness: -9.5 LUFS (Club) v] |
| [TAPE STOP] [STUTTER]    [40Hz SUB DROP]  | [A/B Bypass Master]                   |
+-----------------------------------------------------------------------------------+
7. Project Directory Structure & Deployment
text

k1-studio/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI entrypoint, CORS, WebSocket manager
│   │   ├── models/
│   │   │   └── schemas.py         # Pydantic v2 models matching Section 5
│   │   ├── dsp/
│   │   │   ├── engine.py          # Core 32-bit float Track & Master rendering
│   │   │   ├── regions.py         # Zero-crossing finder & Region FX processors
│   │   │   ├── mastering.py       # Mid/Side, Pultec, Parallel Comp, Tape, LUFS
│   │   │   └── separator.py       # Demucs v4 2-stem & 4-stem wrapper
│   │   └── storage/               # Local workspace for stems & exports
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── TransportBar.tsx
│   │   │   ├── MultiTrackCanvas.tsx
│   │   │   ├── RegionInspector.tsx
│   │   │   └── MasteringConsole.tsx
│   │   ├── store/
│   │   │   └── useDawStore.ts     # Zustand store + Undo/Redo middleware
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
└── docker-compose.yml             # One-command local startup (`docker compose up`)
Acceptance Criteria for Developer Sign-Off
Zero Clicks/Pops: Applying HARD_MUTE or NASA_WALKIE_TALKIE in the middle of a loud sustained bass/synth note must produce zero audible transient clicks at the region entry or exit points (verified via spectrogram inspection).
Sub-85Hz Phase Correlation: The mastered output must exhibit a phase correlation of +1.0 (pure mono) when low-pass filtered at 80 Hz.
True-Peak Compliance: Exported 24-bit WAV files must hit the requested integrated LUFS within ±0.2 LU while never exceeding -0.3 dBTP.
