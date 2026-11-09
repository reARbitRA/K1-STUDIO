---
id: SPEC-002
title: Surgical region FX
type: spec
status: IMPLEMENTING
version: 1.0.0
owner: pair
created: '2026-11-09'
updated: '2026-11-09'
supersedes: []
depends_on:
- SPEC-001
implements: []
traces_to:
- docs/TECHNICAL SPECIFICATION & ARCHITECTURE DOCUMENT.MD
tags:
- k1-studio
- mvp
confidence: high
---

# SPEC-002 — Click-Free Surgical Region FX

## Approval and provenance
Human-approved in advance on 2026-11-09 by the repository owner in the session's
“Human Control Plane Override”; authored by the ARCHITECT under explicit delegation.
This is not agent self-approval. The original architecture reference remains unchanged.
Rules formalize its behavior; otherwise unspecified details are identified as delegated
MVP choices. APPROVED does not mean IMPLEMENTED or VERIFIED.

## 1. Summary
Apply six named non-destructive presets to track or master time regions. Snap boundaries
to nearby zero crossings, blend with raised-cosine micro-crossfades, and preserve duration.

## 2. Motivation
Formalizes reference §4.3 and the click-free developer sign-off. Avoid manual clip slicing
while keeping original assets unchanged.

## 3. User stories
- US-1: An editor applies one of six presets to a selection with one action.
- US-2: A mixer auditions boundary transitions before committing a project edit.

## 4. Scope
### In scope
Crossing detection, complementary fades, wet/dry mixing, all six presets, overlapping
regions, and identical track/master-target processing semantics.
### Out of scope
Custom plugin scripting, tempo detection, length-changing edits, UI and HTTP implementation.

## 5. Behavioral contract
### 5.1 Interfaces
`apply_regions(audio, regions, sample_rate=48000, bpm=None) -> RegionResult(audio, boundaries)`.
Audio buffers follow SPEC-001. Return requested/snapped indices and effective fade lengths.
Regions carry `region_id`, `start_sec`, `end_sec`, `effect_type`, `wet_mix`, `fade_ms`.

### 5.2 Rules
- R1. Require `0 <= start_sec < end_sec <= N/48000`, wet_mix in [0,1], fade_ms in [2,15],
  and finite values. Convert to half-open `[s0,s1)` with `floor(t*48000+0.5)`; require at
  least two selected samples. Reject unknown enum values before rendering.
- R2. Search ±240 samples (5 ms) around each boundary, clipped to input bounds, using
  mid signal `0.5*(L+R)` from the buffer entering that region. A crossing index n is an
  exact zero or precedes a sign change at n+1. Select nearest, ties earlier. Both channels
  share indices. No crossing: retain requested index. Collapse/reversal after snapping:
  revert both to requested bounds. End index N is legal; never read sample N.
- R3. Requested fade F=`floor(fade_ms*48+0.5)` samples. Effective F is min(requested F,
  floor(region sample count/2)). For F≥2, entry `w[k]=0.5*(1-cos(pi*k/(F-1)))`, k=0…F-1;
  exit reverses entry; interior w=1. For F=1, w=0. Composite
  `out=dry + wet_mix*w*(FX(dry)-dry)`. Outside snapped bounds samples are unchanged.
  Endpoint-inclusive indexing makes endpoints exactly dry; no equal-power energy boost.
- R4. Apply overlapping regions in stable JSON array order, each reading the current
  buffer. Reset effect state per region/render, not per processing chunk. Effects return
  exactly the selected sample count, finite float32 stereo. Wet zero is exact bypass.
- R5. HARD_MUTE: wet samples are zero; preset-fixed boundary fade is 3 ms (144 requested
  samples), overriding fade_ms. At wet=1 only the interior outside ramps is exactly zero.
- R6. NASA_WALKIE_TALKIE: second-order Butterworth HPF 520 Hz → second-order LPF 2400 Hz
  → bell 1350 Hz/+3.5 dB/Q2 → soft clip `tanh(10**(14/20)*x)` → compressor
  threshold -28 dBFS, ratio 10:1, attack 1 ms, release 40 ms, no makeup → -7.5 dB trim.
- R7. UNDERWATER_WOMB: fourth-order Butterworth LPF 310 Hz → bell 270 Hz/+4 dB/Q1.8.
- R8. ANALOG_TAPE_STOP: normalized output time u spans [0,1], speed
  `v(u)=max(0.02,(1-u)**1.8)`. Integrate speeds to source sample positions starting at zero;
  interpolate both channels linearly at shared positions. Never wrap/extend the region.
  Apply an internal 5 ms raised-cosine tail fade shortened to fit before outer blending.
- R9. TAPE_STUTTER_DEGRADE: repeat the initial min(region duration,250 ms), or one beat
  (`60/bpm` seconds) if positive finite project BPM is supplied. Shared stereo read
  positions wrap within that loop, with ≤3 ms complementary seam fades shortened to
  half-loop length. LPF cutoff falls geometrically 8000→600 Hz over u. Deterministic
  wow/flutter in cents is `u*(15*sin(2*pi*0.6*t)+5*sin(2*pi*6*t))` for elapsed seconds t;
  read speed is `2**(cents/1200)`. Update second-order LPF cutoff every 48 samples,
  retaining filter state. The source left loop seams/drift unspecified; this fixes them.
- R10. SUB_40HZ_DROP: synthesize identical phase-zero-at-start sine sweeps in both
  channels; frequency falls exponentially 90→36 Hz across the region. Integrate frequency
  to phase. Envelope `10**(-6/20)*exp(-6*u)` defines -6 dBFS envelope amplitude, not an
  exact sampled peak. Add underneath the dry audio; outer wet/fade composition still
  applies. Downstream mixer/master owns headroom; do not clip this effect locally.
- R11. Master regions run once on the summed bus per SPEC-001 R8, never as duplicated
  per-track edits. Backend DSP is authoritative, not waveform overlays.

### 5.3 Data
Exact enum: HARD_MUTE, NASA_WALKIE_TALKIE, UNDERWATER_WOMB, ANALOG_TAPE_STOP,
TAPE_STUTTER_DEGRADE, SUB_40HZ_DROP. Default wet_mix=1; fade_ms=3 for HARD_MUTE,
8 for others. Render metadata stores preset version, requested/snapped bounds, effective
fades and deterministic drift settings. Original PCM never changes.

### 5.4 Errors
`invalid_region`: timing/length/wet/fade/BPM invalid; `unknown_effect`: unsupported enum.
Validation is atomic before rendering. Missing crossings are a supported fallback.

## 6. Acceptance criteria
- AC-1: Given sign-changing, DC, silent, stereo-antiphase and file-edge fixtures, when
  snapping, then R1/R2 bounds, nearest/tie rules and fallback hold exactly.
- AC-2: Given full/short regions, when blended, then R3 weights match within 1e-6,
  outside samples and duration are unchanged, wet zero is identity, and invalid input fails.
- AC-3: Given HARD_MUTE at wet 1, when rendered, then its interior is exactly zero,
  fades request 144 samples, and short regions shorten ramps without overlap.
- AC-4: Given radio impulse and sine tests, when rendered, then R6 topology/settings,
  clipping, compression and trim run in order; 100 Hz and 10 kHz attenuate more than 1350 Hz.
- AC-5: Given underwater impulse/sines, when rendered, then fourth-order 310 Hz LPF and
  270 Hz bell match R7 and 4 kHz attenuation exceeds 40 dB relative to 100 Hz.
- AC-6: Given a periodic region, when tape-stop runs, then positions are nondecreasing,
  speed goes 1→0.02, length is unchanged and the internal wet tail fades to zero.
- AC-7: Given stutter with/without BPM, when repeated renders run, then loop length,
  seam fades, cutoff endpoints and drift follow R9; outputs agree within absolute 1e-6.
- AC-8: Given silence, when sub-drop runs, then channels are identical, initial phase is
  zero, frequency follows 90→36 Hz and the envelope matches R10 within absolute 1e-5.
- AC-9: Given overlapping regions and a master target, when rendered, then array order
  holds, master FX runs once, source buffers remain unchanged and results are finite.
- AC-10: Given 2-second sustained 55/110/220 Hz signals at -3 dBFS, when HARD_MUTE and
  radio apply at 0.5–1.5s, then composite endpoints agree with dry within 1e-6. Retain
  waveform/spectrogram artifacts and human audition evidence of no audible entry/exit
  click; array tests alone do not establish perceptual sign-off.

## 7. Non-functional requirements
Deterministic fixed-version/settings output; no uncontrolled random state. Preview speed
belongs to SPEC-004. Crossing detection alone cannot guarantee no clicks on arbitrary
stereo signals: both channels must be crossfaded, measured and auditioned.

## 8. Security considerations
Allowlisted enums only, no evaluated preset code, no source-file writes. Validate bounds
before allocation, and honor admission limits in SPEC-004.

## 9. Open questions / delegated choices
R1–R11 settle previously unspecified crossing channel/ties, overlap order, short-region
handling, clipping curve, loop seams/drift and sub envelope under explicit delegation.
No blocking algorithm question. AC-10 still requires human listening evidence before
verification; no universal “zero clicks” theorem is claimed.

## 10. Verification plan
Planned (not yet implemented): `.venv/bin/python -m pytest tests/dsp/test_regions.py -v`.
AC-10 additionally requires listening/spectrogram review.

| AC | Required test name in tests/dsp/test_regions.py |
| --- | --- |
| AC-1 | test_ac_1_zero_crossing_boundaries |
| AC-2 | test_ac_2_complementary_fades |
| AC-3 | test_ac_3_hard_mute |
| AC-4 | test_ac_4_nasa_radio |
| AC-5 | test_ac_5_underwater |
| AC-6 | test_ac_6_tape_stop |
| AC-7 | test_ac_7_stutter_degrade |
| AC-8 | test_ac_8_sub_drop |
| AC-9 | test_ac_9_overlap_and_targets |
| AC-10 | test_ac_10_click_boundary_fixtures |

## 11. Trace
SPEC-001 → SPEC-002; PLAN-001 → T-002. Task lists planned files; TRACE records existing
artifacts only until implementation. No product execution evidence yet.
