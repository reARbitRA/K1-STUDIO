---
id: SPEC-001
title: Core DSP and channel strip
type: spec
status: IMPLEMENTING
version: 1.0.0
owner: pair
created: '2026-11-09'
updated: '2026-11-09'
supersedes: []
depends_on: []
implements: []
traces_to:
- docs/TECHNICAL SPECIFICATION & ARCHITECTURE DOCUMENT.MD
tags:
- k1-studio
- mvp
confidence: high
---

# SPEC-001 — Core DSP Engine, Track Mixer, and Channel Strip

## Approval and provenance
Human-approved in advance on 2026-11-09 by the repository owner in the session's
“Human Control Plane Override”; authored by the ARCHITECT under explicit delegation.
This is not agent self-approval. The original architecture reference is preserved
unchanged. Numbered rules formalize its behavior; details absent from the source are
identified as delegated MVP contract choices. APPROVED is not IMPLEMENTED or VERIFIED.

## 1. Summary
Render non-destructive stereo mixes at 48,000 Hz using float32 audio buffers. Each track
runs gain, polarity, channel EQ/compression, region processing, and equal-power pan
before solo/mute-aware summation and pre-master headroom scaling.

## 2. Motivation
Formalizes the architecture reference §§3, 3.1, 4, 4.2 and the track-node/summing-bus
routing diagram. Region algorithms and mastering are separate contracts, not duplicated.

## 3. User stories
- US-1: As an editor, I mix stems without changing the uploaded originals.
- US-2: As a mixer, I control gain, phase, EQ, compression, pan, mute, and solo predictably.

## 4. Scope
### In scope
Canonical audio buffers, ingestion conversion, track controls, summing, headroom,
channel-strip DSP, and deterministic offline execution with NumPy/SciPy/Pedalboard.
### Out of scope
Separation/HTTP/UI (SPEC-004), region implementations (SPEC-002), mastering/export
(SPEC-003), recording, third-party plugin hosting, and sample-rate selection.

## 5. Behavioral contract
### 5.1 Interfaces
Logical Python interfaces, with module location selected in PLAN-001:
- `canonicalize(audio, input_sample_rate) -> AudioBuffer`.
- `render_track(audio, track_settings, region_processor) -> AudioBuffer`.
- `mix_tracks(track_buffers, track_settings) -> MixResult(audio, pre_master_gain_db)`.
`AudioBuffer` is finite float32 NumPy data of shape `(N, 2)` at 48000 Hz. Native float64
filter coefficients/intermediates are allowed; stage outputs must return float32.
Empty projects return a `(0,2)` buffer, not NaNs or an exception.

### 5.2 Rules
- R1. Decode locally, duplicate a mono channel to stereo; reject more than two channels.
  Resample using anti-aliased rational polyphase conversion (SciPy `resample_poly`,
  reduced integer up/down factors). Preserve duration to within one output sample;
  input originals and their metadata remain unmodified. No integer PCM clipping in DSP.
- R2. Reject nonpositive/noninteger sample rates, malformed dimensions, nonfinite samples,
  nonfinite parameters, and out-of-range controls before processing. Errors carry field
  names but no audio content. Do not silently clamp invalid project settings.
- R3. Track order is pre-gain → polarity invert → HPF → de-mud → presence → de-fizz →
  compressor → region FX (SPEC-002) → pan. Gain multiplier is `10**(gain_db/20)`;
  phase invert multiplies both channels by -1. Each stage can be identity-tested.
- R4. Channel strip uses these exact ranges/defaults. Frequencies and Q are fixed except HPF.

  | Control | Range / fixed characteristic | MVP default |
  | --- | --- | --- |
  | Input gain | -24 to +12 dB | 0 dB |
  | Phase invert | Boolean | false |
  | HPF | 20–500 Hz, second-order Butterworth, 12 dB/oct | 20 Hz |
  | De-mud bell | 290 Hz, Q 1.6, -6 to +3 dB | -2 dB |
  | Presence bell | 2650 Hz, Q 1.2, -6 to +6 dB | 0 dB |
  | De-fizz bell | 4850 Hz, Q 2.5, -6 to 0 dB | -1.8 dB |
  | Compressor threshold | -40 to 0 dBFS | -18 dBFS |
  | Ratio | 1–10 | 4 |
  | Attack | 1–100 ms | 25 ms |
  | Release | 20–500 ms | 120 ms |

  Bells use peaking biquads with stated center/Q/gain. Use Pedalboard gain/EQ/compression
  and SciPy for missing filter primitives. No hidden automatic makeup gain. Initialize
  processor state once per render; reset between renders, not on each processing block.
- R5. For `pan p ∈ [-1,1]`, `theta=(p+1)*pi/4`, `GL=cos(theta)`, `GR=sin(theta)`.
  Apply GL to left, GR to right without folding stereo to mono. Center is
  `1/sqrt(2)` per channel (-3.0103 dB); endpoints preserve one channel and null the other.
- R6. A muted track contributes zero even if soloed. If any track is soloed, include only
  soloed, nonmuted tracks; otherwise include all nonmuted tracks. Track buffers start at
  time zero; right-pad shorter tracks with zeros to the longest project track duration,
  including muted tracks, so mute/solo never changes the timeline duration.
- R7. Accumulate finite track samples without clipping. For summed absolute peak P,
  apply `g=10**(-6/20)/max(1,P)` to both channels. Thus even quiet sums receive 6 dB
  attenuation and hot sums cannot exceed -6 dBFS. Report `20*log10(g)`; silence retains
  its length with no division by zero. This resolves the source's “scaling/normalization”
  ambiguity as attenuation-only safety scaling, never upward normalization.
- R8. Master-target regions run on the pre-master sum after R7 and before SPEC-003;
  they are not cloned onto each track. Freeze graph/settings for each render; edits do
  not mutate an in-flight job or the uploaded buffers. Whole-project duration is fixed.

### 5.3 Data
Track settings: `track_id`, name, server-resolved `file_path`, `gain_db`, `pan`, `mute`,
`solo`, `phase_invert`, `channel_strip`, `regions`. All IDs are unique within a project.
Channel strip fields are `hp_hz`, `de_mud_db`, `presence_db`, `de_fizz_db`,
`comp_threshold_db`, `comp_ratio`, `comp_attack_ms`, `comp_release_ms`.
Render metadata records sample rate, duration, dependency versions, and actual safety gain.

### 5.4 Errors
DSP validation raises a typed `invalid_audio` or `invalid_parameter` error; missing local
assets produce `asset_not_found`. SPEC-004 maps these to HTTP errors. No partial mix is
presented as successful output. Unsupported channels are `unsupported_audio`.

## 6. Acceptance criteria
- AC-1: Given mono/stereo fixtures at 44.1/48/96 kHz, when canonicalized, then outputs
  are finite float32 `(N,2)`/48kHz, duration error ≤1 sample, and originals are unchanged.
- AC-2: Given known stereo samples, when gain and phase stages run in isolation, then
  analytical gain/inversion results agree within absolute 1e-6; invalid input is rejected.
- AC-3: Given isolated pan tests at -1, 0, +1, when rendered, then coefficients match R5
  within 1e-6 and `GL**2+GR**2` equals 1 within 1e-6.
- AC-4: Given mixed mute/solo flags and unequal lengths, when summed, then inclusion,
  zero-padding, timeline length, and all-muted silence follow R6 exactly.
- AC-5: Given quiet, overloaded, and silent sums, when safety scaling runs, then gain
  follows R7 within 1e-6 and peak is ≤`10**(-6/20)+1e-6` without clipping.
- AC-6: Given isolated filter impulse/sine tests, when each EQ runs, then center response
  agrees with its peaking-biquad design within 0.25 dB and HPF steady-state attenuation
  at half cutoff is at least 10 dB relative to passband; zero-gain bells are identity.
- AC-7: Given long steady signals below/above threshold, when compressed at ratio 1 or
  4, then ratio 1 is identity within 1e-6 and settled dB output slope at ratio 4 agrees
  with 1/4 within 0.05. Attack/release/range endpoints are forwarded and validated.
- AC-8: Given injected spy stages and repeated renders, when the same snapshot renders,
  then R3/R8 order is observed, source data is unchanged, output is repeatable within
  1e-6, and state from previous renders does not leak.

## 7. Non-functional requirements
No full-scale clipping before mastering; identical graph/assets/versions give deterministic
output within stated tolerances. Process input in bounded chunks where filter semantics
allow; do not claim real-time performance before measurements exist. No speed SLA is
inferred from the region-preview SLA in SPEC-004.

## 8. Security considerations
Only backend-resolved workspace assets reach DSP. Validate dimensions and finite values
before allocation/processing. No shell commands, external fetches, or user-controlled
plugin execution; apply quality/SECURITY-BASELINE.md.

## 9. Open questions / delegated choices
The source did not define defaults, mono/channel policy, stereo-pan interpretation,
filter primitive selection, headroom normalization, or unequal-length behavior. R1–R8
settle these under the human's explicit architecture delegation; changes require a new
DRAFT revision, not implementation-time guessing. No blocking question for core DSP.

## 10. Verification plan
Planned command (not executable until T-001 installs product dependencies/tests):
`.venv/bin/python -m pytest tests/dsp/test_core.py -v`.

| AC | Required test name in tests/dsp/test_core.py |
| --- | --- |
| AC-1 | test_ac_1_canonical_audio |
| AC-2 | test_ac_2_gain_phase_validation |
| AC-3 | test_ac_3_equal_power_pan |
| AC-4 | test_ac_4_mute_solo_padding |
| AC-5 | test_ac_5_headroom |
| AC-6 | test_ac_6_channel_eq |
| AC-7 | test_ac_7_channel_compression |
| AC-8 | test_ac_8_order_and_immutability |

## 11. Trace
PLAN-001 → T-001 → this spec. Planned files/tests are in the task; TRACE contains only
existing artifacts until implementation. No product tests, commits, or PRs exist yet.
