---
id: SPEC-003
title: Analog master bus and WAV export
type: spec
status: IMPLEMENTING
version: 1.0.0
owner: pair
created: '2026-11-09'
updated: '2026-11-09'
supersedes: []
depends_on:
- SPEC-001
- SPEC-002
implements: []
traces_to:
- docs/TECHNICAL SPECIFICATION & ARCHITECTURE DOCUMENT.MD
tags:
- k1-studio
- mvp
confidence: high
---

# SPEC-003 — Analog Master Bus and WAV Delivery

## Approval and provenance
Human-approved in advance on 2026-11-09 by the repository owner in the session's
“Human Control Plane Override”; authored by the ARCHITECT under explicit delegation.
This is not agent self-approval. The original architecture reference remains unchanged.
Rules formalize its behavior; otherwise unspecified details are identified as delegated
MVP choices. APPROVED does not mean IMPLEMENTED or VERIFIED.

## 1. Summary
Master the pre-scaled stereo mix through M/S bass narrowing, fixed-shape musical EQ,
parallel compression, asymmetric tape-style saturation, loudness normalization and
true-peak limiting. Export validated 24-bit WAV with before/after loudness/peak telemetry.

## 2. Motivation
Formalizes reference §4.4, master_bus JSON in §5.1, and final sign-off requirements.
“Pultec”, “SSL”, “1176” and “Studer A800” describe the specified approximations, not licensed
circuit emulation or evidence that any named hardware has been modeled accurately.

## 3. User stories
- US-1: A mixer narrows unstable low-frequency stereo energy while retaining upper width.
- US-2: A user selects streaming/club/aggressive loudness and downloads compliant WAV.

## 4. Scope
### In scope
Offline master chain, parameter defaults, loudness/true-peak measurements, atomic PCM_24
export, and source-required secondary dithered PCM_16 export.
### Out of scope
Hardware emulation fidelity, real-time zero-latency mastering, MP3, multichannel delivery,
or a promise that every signal can satisfy arbitrary loudness and peak goals together.

## 5. Behavioral contract
### 5.1 Interfaces
`master(audio, settings) -> MasterResult(audio, telemetry)` consumes SPEC-001 stereo
48000 Hz float32. `export_wav(result, bit_depth=24) -> workspace_asset` creates a complete
file only on success. Audition-only A/B bypass returns the same pre-master input
without master stages; it is not an export setting. Export always uses the full chain
and its compliance gates, regardless of the UI audition toggle.

### 5.2 Rules
- R1. Execute in strict order: M/S → EQ → parallel compression → tape → integrated
  loudness gain → true-peak limiter → PCM encoding and final verification. Never move
  loudness gain after the limiter. Pre-master headroom comes from SPEC-001, not a second
  hidden 6 dB attenuation in this module.
- R2. Encode `M=0.5*(L+R)`, `S=0.5*(L-R)`. Design fourth-order Butterworth HPF at 85 Hz,
  apply only to S with SciPy `sosfiltfilt`, multiply filtered S by width in [0,1.5],
  default 1.15, and decode `L=M+S'`, `R=M-S'`. M is unchanged by this stage. Forward/
  backward filtering is zero phase and squares the one-pass magnitude response; do not
  label its effective rolloff as a one-pass fourth-order response. Short buffers use
  explicit symmetric padding to the required filter pad length, then crop to N; silence
  and empty buffers return unchanged. Width zero gives identical channels.
- R3. EQ stages in order, no automatic gain compensation:

  | Stage | Frequency | Gain | Q / topology |
  | --- | --- | --- | --- |
  | Sub-rumble HPF | 28 Hz | — | second-order Butterworth |
  | Low shelf | 62 Hz | +2.2 dB | Q 0.7 |
  | Mud bell | 285 Hz | -2.5 dB | Q 1.5 |
  | Presence bell | 2700 Hz | +1.8 dB | Q 1.2 |
  | Whistle bell | 4800 Hz | -2.2 dB | Q 2.5 |
  | Air shelf | 10500 Hz | +1.6 dB | Q 0.7 |

  Use biquad bell/shelf primitives; response is the designed cascade, not an exact
  hardware response. Exposed EQ gains may vary -12…+12 dB; frequencies/Q remain fixed.
- R4. Feed the same EQ output to two parallel compressors. A: threshold -16 dBFS,
  ratio 3:1, attack 25 ms, release 120 ms. B: -28 dBFS,8:1,5 ms,60 ms.
  Output `(1-c)*A+c*B`, c default 0.18, range [0,1]; no additional dry path, makeup gain
  or serial A→B processing. Initialize state per render, preserve it through chunks.
- R5. Tape per sample is `(tanh(d*x+alpha)-tanh(alpha))/tanh(d)`, d in [1,2],
  default 1.22, alpha fixed 0.035. Apply independently with identical settings to both
  channels. Zero input maps to zero; do not substitute symmetric tanh or add a DC offset.
- R6. Measure integrated LUFS with `pyloudnorm.Meter(48000)` (ITU-R BS.1770-4). Allowed
  targets are -14.0, -9.5 (default), -8.0 LUFS. Normalize gain to target, then limit with
  45 ms release and ceiling -0.3 dBTP. Meter input to mastering and final encoded output;
  telemetry also includes sample peaks and applied gain. Gated-out/silent loudness is
  represented as JSON null plus `loudness_status: unmeasurable`, never NaN/Infinity.
- R7. A sample-peak limiter alone is insufficient. Use at least 4x oversampled true-peak
  detection with band-limited interpolation, gain lookahead, and output verification.
  Preserve alignment/length by compensating latency. Quantization can change peak/LUFS;
  remeasure the decoded exported PCM, not merely the pre-encoding buffer. Successful
  nonsilent exports must be within ±0.2 LU of target and ≤-0.3 dBTP including intersample
  peaks. If these cannot both be met without changing approved settings, fail with
  `loudness_target_unreachable`; never publish a misleading compliant result.
- R8. Default export is 48kHz stereo RIFF/WAV PCM_24 using soundfile/libsndfile. Secondary
  bit_depth=16 uses PCM_16 with TPDF dither: sum two independent uniform(-0.5,0.5) values
  in integer-LSB units before quantization. Store a per-export fixed seed in metadata
  for reproducibility. No dither is required for PCM_24 in this MVP. Clip protection must
  not be implemented by integer overflow. Encode to a temporary file, verify, then
  atomically publish an opaque workspace download handle.
- R9. Silence exports zeros; skip normalization and dither, and emit unmeasurable LUFS. For nonzero
  audio shorter than 400 ms, measure a zero-padded 400 ms analysis copy but retain actual
  duration. Telemetry marks `analysis_padded: true`; final loudness target verification
  uses the same declared padding policy. Nonfinite input/settings fail before export.

### 5.3 Data
`master_bus`: `mono_bass_cutoff_hz` fixed 85, `stereo_width` 1.15,
`pultec_low_boost_db` 2.2, `mud_cut_db` -2.5, `mid_bite_db` 1.8,
`air_boost_db` 1.6, `parallel_comp_mix` 0.18, `tape_drive` 1.22,
`target_lufs` -9.5, `ceiling_db` fixed -0.3; optional master `regions` per SPEC-002.
Telemetry: before/after integrated_lufs, sample_peak_dbfs, true_peak_dbtp, target_lufs,
normalization gain, safety gain, limiter reduction, sample count, analysis policy,
bit depth, DSP/library versions and optional dither seed. All JSON numbers must be finite.

### 5.4 Errors
`invalid_master_settings`, `invalid_audio`, `loudness_target_unreachable`, `export_failed`.
No partial download URL on failure. Workspace cleanup removes temporary files on errors.

## 6. Acceptance criteria
- AC-1: Given stereo impulses/sines and short buffers, when M/S runs, then M is preserved,
  width zero is mono, filter response matches the R2 design within 0.25 dB, alignment and
  length are unchanged, and finite outputs result without padding exceptions.
- AC-2: Given 10-second mono 40 Hz plus stereo 2 kHz calibration audio, when processed
  and zero-phase low-passed at 80 Hz for analysis (trim 1 second at each edge), then
  L/R correlation is ≥0.9999 and rounds to +1.0. Also retain the arbitrary-side-only LF
  counterexample demonstrating the source's universal pure-mono claim is not guaranteed.
- AC-3: Given isolated EQ tests, when the cascade runs, then the six settings/topologies
  match R3 and response matches the designed cascade within 0.25 dB at test frequencies.
- AC-4: Given compressor spies and steady tones, when parallel compression runs, then
  both branches receive identical input, parameters match R4, c=0/1 selects A/B exactly,
  and default output equals `0.82*A+0.18*B` within absolute 1e-6.
- AC-5: Given x across [-2,2] and d endpoints/default, when tape runs, then R5 analytical
  output agrees within 1e-6, zero maps to zero and positive/negative symmetry differs.
- AC-6: Given feasible ≥10-second loudness fixtures, when exported at each target, then
  independent measurements of decoded PCM_24 are within ±0.2 LU and ≤-0.3 dBTP.
  Include intersample-overs fixtures that distinguish true peak from sample peak.
- AC-7: Given silence, short/nonfinite input and an infeasible fixture, when mastered,
  then R9 policies are honored; unreachable/nonfinite failures return typed errors and
  do not publish files. Short-file telemetry explicitly marks analysis padding.
- AC-8: Given successful 24/16-bit exports, when reopened, then subtype/rate/channels/
  sample count match R8; 16-bit fixed-seed dither is reproducible and zero-mean over a
  long fixture, while 24-bit processing never uses integer intermediates before encoding.
- AC-9: Given injected stages and A/B bypass, when rendered, then R1 order and telemetry
  are correct, state does not leak across renders and failed verification cleans up files.

## 7. Non-functional requirements
Retain float32 stage boundaries with float64 metering/filter coefficients allowed.
Use an independent true-peak check in acceptance tests, not only the limiter's own
reported peak. No unmeasured “analog quality”, throughput or hardware-equivalence claim.

## 8. Security considerations
Generated server paths only, atomic output publication, bounded input/analysis buffers,
no embedded original absolute paths in download responses. Original stems remain immutable.

## 9. Source inconsistency / delegated resolutions
A finite-order Butterworth HPF attenuates but cannot eliminate *all* side energy below
85 Hz. The source's “100% mono / correlation +1.0 for arbitrary material” does not follow
from its required filter. Preserve the exact filter and test its response; AC-2 makes the
calibration criterion measurable without falsely promising a brickwall. Exact arbitrary-
material sub-bass mono would require a separate approved revision/decision, not silently
adding a different filter. This limitation is part of the delegated formalization.
Likewise arbitrary signals cannot always meet both LUFS and peak targets; R7 requires
an honest failure rather than weakening either success criterion. Defaults/ranges absent
from the source, short-buffer handling, true-peak verification and dither are now explicit.

## 10. Verification plan
Planned: `.venv/bin/python -m pytest tests/dsp/test_mastering.py -v`.
No measured compliance or export evidence exists yet.

| AC | Required test name in tests/dsp/test_mastering.py |
| --- | --- |
| AC-1 | test_ac_1_ms_filter_and_width |
| AC-2 | test_ac_2_low_band_correlation |
| AC-3 | test_ac_3_master_eq |
| AC-4 | test_ac_4_parallel_compression |
| AC-5 | test_ac_5_asymmetric_tape |
| AC-6 | test_ac_6_lufs_true_peak_export |
| AC-7 | test_ac_7_silence_short_and_failure |
| AC-8 | test_ac_8_pcm_formats_and_dither |
| AC-9 | test_ac_9_order_bypass_and_telemetry |

## 11. Trace
Dependencies SPEC-001 and SPEC-002; PLAN-001 → T-003. Existing documents are in TRACE;
source/test paths and execution evidence will be added when actually created/executed.
