---
id: SPEC-004
title: API, stem separation and frontend UI
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
- SPEC-003
implements: []
traces_to:
- docs/TECHNICAL SPECIFICATION & ARCHITECTURE DOCUMENT.MD
tags:
- k1-studio
- mvp
confidence: high
---

# SPEC-004 — Local API, Stem Separation, and Dark-Studio UI

## Approval and provenance
Human-approved in advance on 2026-11-09 by the repository owner in the session's
“Human Control Plane Override”; authored by the ARCHITECT under explicit delegation.
This is not agent self-approval. The original architecture reference remains unchanged.
Rules formalize its behavior; otherwise unspecified details are identified as delegated
MVP choices. APPROVED does not mean IMPLEMENTED or VERIFIED.

## 1. Summary
Expose local audio ingestion, Demucs jobs, region audition and full render through
FastAPI and a React/TypeScript single-screen workstation. Keep the immutable project
graph in Zustand and delegate final audio processing to SPEC-001–SPEC-003.

## 2. Motivation
Formalizes source §§2, 3, 3.1, 4.1, 5, 6 and 7. Preserve low-friction controls and
local-first privacy; make the formerly example-only JSON/API precise enough to implement.

## 3. User stories
- US-1: A user imports a stereo master directly or splits it into two/four editable stems.
- US-2: An editor selects/labels regions, undoes/redoes edits and auditions them promptly.
- US-3: A mixer adjusts track/master controls and downloads a mastered WAV with telemetry.

## 4. Scope
### In scope
FastAPI/Pydantic v2/Uvicorn, worker isolation, Demucs v4, project JSON, opaque assets,
progress WebSocket, React 18+/TypeScript/Vite/Tailwind/WaveSurfer.js v7, Zustand,
lucide-react, synchronized transport/meters, and local compose/dev startup.
### Out of scope
Authentication/multitenancy, cloud audio upload, collaborative editing, remote model
training, recording, a general-purpose plugin host, mobile layout, or real-time parity
between basic Web Audio transport and the offline analog master chain.

## 5. Behavioral contract
### 5.1 Interfaces
API prefix `/api/v1`; JSON UTF-8 except multipart upload and WAV responses. Unknown JSON
fields are rejected, defaults materialize into the canonical project graph. Strict finite
numbers/booleans; do not accept NaN, Infinity, string booleans or arbitrary file paths.

| Method/path | Request | Success |
| --- | --- | --- |
| POST /api/v1/ingest/upload | multipart file; optional project_id | 201 UploadResult; one direct track |
| POST /api/v1/ingest/split-stems | {project_id, track_id, mode: 2stem or 4stem} | 202 {job_id, status: queued, websocket_url} |
| WS /ws/jobs/{job_id} | existing job id | JSON progress events |
| POST /api/v1/preview/region | {project, target_type: track or master, track_id: string or null, region_id, optional bypass_master default false} | 200 audio/wav slice |
| POST /api/v1/project/render | canonical project JSON, optional export_bit_depth default 24 | 200 RenderResult |
| GET /api/v1/assets/{asset_id} | opaque issued id | 200 WAV/attachment, supports byte ranges |

`UploadResult={asset_id, file_path, duration_sec, sample_rate:48000, channels:2,
waveform_peaks, project}`. `file_path` is a server-issued workspace handle, not a client
filesystem authority. `waveform_peaks={bins:512, channels:[left_bins,right_bins]}`; each
bin is `[min,max]` in finite float units from equal-duration buckets, zero-pad empty
buckets. Return waveform data once canonicalized, not after separation.
`RenderResult={project_id, downloads:[{asset_id,url,bit_depth}], telemetry}` with
SPEC-003 before/after LUFS, sample/true peaks and statuses. All returned URLs are relative.
`Progress={job_id,status,progress,stage,error,project}`: status queued/running/succeeded/
failed, progress monotonic [0,1], stage nonsecret string, error null or error envelope,
project null except succeeded. Terminal event is authoritative and replayed on reconnect.

### 5.2 Rules
- R1. Canonical project: `project_id` (opaque unique ID), `sample_rate` fixed 48000,
  `master_bus` (SPEC-003 settings including optional regions), optional positive BPM,
  and ordered `tracks` (SPEC-001). Track/region IDs unique in their scopes; all referenced
  handles belong to that project. Region timing cannot exceed the owning track duration
  or summed project duration for master targets. Missing optional settings take spec
  defaults, required IDs/times/assets do not. Pydantic schemas generate OpenAPI.
- R2. Preserve the source sample fields exactly: tracks contain `track_id`, name,
  file_path, gain_db, pan, mute, solo, phase_invert, channel_strip, regions. Region fields
  and six enums are SPEC-002; add compressor attack/release defaults from SPEC-001.
  Master fields, defaults/ranges, loudness and ceiling are SPEC-003. `mono_bass_cutoff_hz`
  remains fixed 85 and `ceiling_db` fixed -0.3 in the MVP, not misleading adjustable knobs.
- R3. Upload accepts WAV, FLAC and AIFF decodable by libsndfile; reject unsupported
  codecs/channels and malformed content regardless of extension. Maximum 256 MiB encoded,
  30 minutes decoded per asset, 8 tracks/project, 128 regions/track and 128 master regions.
  Bound upload streaming and decoded allocation; reject before storing partial assets
  when possible and clean up on failure. Generate IDs/server filenames; no user path joins.
- R4. Direct import adds one track. 2stem runs local `htdemucs`; output Vocals and
  Instrumental, the latter summed from that same inference's Drums+Bass+Other buffers,
  never separate inference or magnitude reconstruction. 4stem uses `htdemucs_ft` and
  returns Vocals, Drums, Bass, Other. Convert outputs to SPEC-001 buffers, align/crop/pad
  to original duration and replace the imported track atomically on success. Failure
  preserves the original track and graph; no half-populated project. This component sum
  preserves inference-phase relationships, not guaranteed perfect reconstruction of input.
- R5. At most one heavy separation/render/preview worker job executes concurrently;
  separation returns asynchronously, render/preview await worker results without blocking
  the event loop. Busy operations return 409 busy; no unbounded queue. Unit tests use a
  deterministic fake separator, with separately opt-in real-model smoke tests. Model
  weights are cached outside Git and provisioned locally with license/provenance notes;
  missing weights/accelerator setup returns 503 model_unavailable, no hidden downloads.
- R6. Job events start queued/0, then running, then succeeded/1 or failed with last
  progress. If Demucs exposes no fine progress, stage boundaries are acceptable; never
  fabricate percent accuracy. WS sends initial state, updates and terminal event then
  closes normally. Unknown job closes with code 1008; worker restart may lose jobs in
  this local MVP, reported as unknown instead of false success. Validate WS Origin too.
- R7. Region preview uses the complete project snapshot, selected target/region, and
  timeline slice `[max(0,start_sec-2), min(project_duration,end_sec+2)]`. Run sufficient
  preceding DSP context (or the full graph) before cropping so stateful filters match
  full-render audition; the context is not an extra 2 seconds of published audio.
  Apply selected/all existing region edits and master chain (unless audition-only
  bypass_master is true, which returns the pre-master region-processed mix); return
  stereo 48kHz WAV
  with X-Start-Sec and X-End-Sec headers for transport alignment. Do not apply the same
  selected preset twice. Authoritative preview replaces basic dry transport while played.
- R8. Render validates and snapshots the graph, executes SPEC-001→SPEC-002 bus placement
  →SPEC-003, and returns only verified files. Failures use §5.4; no partial download URLs.
  Primary download is PCM_24; export_bit_depth=16 selects the dithered secondary format.
- R9. React screen has four zones: transport/top bar; 240px track headers with aligned
  multi-track waveform canvas; bottom-left region inspector; bottom-right mastering
  console. Theme: background #0D0E12, panels #16181F, crimson #E11D48, cyan #06B6D4.
  At desktop 1440×900 and 1920×1080 with up to four visible tracks, all four zones fit
  without page scroll. Extra tracks scroll inside the canvas/header region in sync.
- R10. Transport exposes Import, 2-/4-Stem Split, Play/Pause, timecode, LUFS, Undo, Redo,
  Preview Region and Export WAV. Track headers expose name, gain, pan, mute, solo, phase
  and channel-strip controls. WaveSurfer v7 uses Regions/Timeline/Minimap plugins; all
  tracks share one transport clock and zoom/scroll/time axis. Web Audio supplies basic
  gain/pan/mute/solo and meters, not an unsupported claim of exact master-chain DSP parity.
- R11. Inspector allows numerical start/end seconds and six labeled one-tap preset
  buttons, wet/fade controls, selected-track or master target. Master console exposes
  sub-mono status, width, four EQ macros, parallel blend, tape drive, target loudness
  (-14/-9.5/-8), and A/B bypass. Numeric controls validate exact backend ranges and
  reject invalid edits without corrupting state. Knobs have keyboard/numeric alternatives.
- R12. Zustand maintains an immutable project graph with transaction-level undo/redo;
  one drag gesture/one preset click is one history step. New edits after undo clear redo.
  Freeze a snapshot per API request. Save/reload canonical JSON via local browser
  persistence; waveform caches, decoded AudioBuffers and transient job state are not
  serialized into the graph. The A/B toggle is transient audition state, sent only as
  preview bypass_master; it never bypasses export compliance. Show loading/error/success
  states without discarding edits.
- R13. Only relative API/WS/download URLs in browser code. Vite binds 0.0.0.0 and proxies
  /api and /ws to the backend; allow Arena's assigned preview host without a wildcard
  backend CORS policy. Default local backend binds loopback unless explicitly configured
  for preview/container use. Local services are unauthenticated and must not be exposed
  to public networks; protect origin/host and workspace boundaries, including WebSockets.
  Provide documented local dev commands and `docker compose up` once implemented.

### 5.3 Data
Example render graph (defaulted fields can be omitted on input, not in canonical output):
```json
{
  "project_id": "hich_session_01",
  "sample_rate": 48000,
  "master_bus": {
    "mono_bass_cutoff_hz": 85.0, "stereo_width": 1.15,
    "pultec_low_boost_db": 2.2, "mud_cut_db": -2.5, "mid_bite_db": 1.8,
    "air_boost_db": 1.6, "parallel_comp_mix": 0.18, "tape_drive": 1.22,
    "target_lufs": -9.5, "ceiling_db": -0.3, "regions": []
  },
  "tracks": [{
    "track_id": "trk_vocals", "name": "Vocals", "file_path": "asset_issued_by_server",
    "gain_db": 1.5, "pan": 0.0, "mute": false, "solo": false, "phase_invert": false,
    "channel_strip": {"hp_hz": 75.0, "de_mud_db": -2.0, "presence_db": 2.5,
      "de_fizz_db": -1.8, "comp_threshold_db": -18.0, "comp_ratio": 4.0,
      "comp_attack_ms": 25.0, "comp_release_ms": 120.0},
    "regions": [{"region_id": "reg_01", "start_sec": 4.12, "end_sec": 4.88,
      "effect_type": "HARD_MUTE", "wet_mix": 1.0, "fade_ms": 3.0}]
  }]
}
```
This is a schema example, not an existing asset/session. The source's absolute file_path
example becomes a server-issued handle; a user cannot request arbitrary workspace paths.

### 5.4 Errors
Envelope: `{error:{code:string,message:string,field:string|null}}`; no stack traces,
absolute storage paths, audio or secrets. Use the same shape for schema/domain failures.

| Status | Code / condition |
| --- | --- |
| 404 | project_not_found, asset_not_found, region_not_found |
| 409 | busy, loudness_target_unreachable |
| 413 | upload_too_large, duration_limit, project_limit |
| 415 | unsupported_audio |
| 422 | invalid_request, invalid_parameter, invalid_region, unknown_effect, invalid_audio |
| 503 | model_unavailable |
| 500 | processing_failed, export_failed (sanitized) |

## 6. Acceptance criteria
- AC-1: Given valid/invalid project JSON, when parsed, then defaults/ranges/enums/unique
  IDs/asset ownership follow R1/R2, generated OpenAPI matches, invalid requests return 422.
- AC-2: Given mono/stereo WAV/FLAC/AIFF upload, when accepted, then 201 includes canonical
  48kHz audio, 512-bin finite stereo peaks and one direct track; source remains unchanged.
- AC-3: Given fake Demucs component buffers, when 2stem/4stem jobs complete, then model
  selection, stem names/order, exact component summation, alignment and atomic graph
  replacement follow R4; failure/missing model leaves original data intact.
- AC-4: Given queued/running/success/failure jobs, when WS connects/reconnects, then
  R6 event schema, monotonic progress, terminal replay and unknown-job behavior hold.
- AC-5: Given a selected boundary region, when previewed, then crop limits/headers,
  applied FX/master and returned WAV match R7; compare to full-render crop within 1e-5.
- AC-6: Given feasible and failing render snapshots, when export is requested, then
  R8 returns verified relative URLs/telemetry only on success, correct PCM format and
  sanitized errors otherwise; later UI edits cannot change the snapshot.
- AC-7: Given malicious paths, origins, oversize content, bad codec, NaN or limits, when
  HTTP/WS requests arrive, then R3/R13 reject them without external file access, hidden
  network/model download, partial project mutations, or a blocked event loop.
- AC-8: Given canonical initial state, when numeric/drag/preset edits, undo/redo and reload
  run, then R12 history and persisted graph are exact and transient buffers are excluded.
- AC-9: Given the two desktop viewport sizes with four tracks, when UI loads, then four
  zones, 240px headers, colors and controls match R9–R11; document body does not scroll.
- AC-10: Given multiple tracks and master/track region edits, when transport, seeking,
  mute/solo/phase, preview or A/B runs, then controls update the same graph, waveforms
  remain synchronized to within one animation frame and preview is not double-applied.
- AC-11: Given keyboard-only interaction and mocked slow/failing jobs, when import,
  edits, audition and export run, then controls are operable/labeled, focus remains usable,
  progress/errors are visible and prior edits are preserved.
- AC-12: Given the benchmark in §7, when preview requests run, then latency meets the
  stated budget and benchmark output records hardware, versions and latency distribution.

## 7. Non-functional requirements
Preview benchmark: four resident stereo tracks, 10-second total project, one selected
1-second radio region, all master stages enabled, no concurrent separation. After 20
warmups measure 100 sequential local requests from request acceptance to WAV response
completion, on ≥4 CPU cores/8 GiB RAM; p95 <300 ms. Report median/p95/max/hardware;
no cold model loading is excluded from a separation claim because none is made here.
Peak decoded buffers obey R3 limits. No product speed/coverage/UX claim exists before
benchmark/tests execute. If the budget fails, optimize or propose a revision; do not omit
DSP stages or silently return dry audio. Offline source privacy is mandatory.

## 8. Security considerations
Local-only trust boundary, explicit origins, no traversal/symlink escapes, opaque assets,
workspace quotas, worker admission, sanitized errors, no user shell arguments or evaluated
JSON, no external audio transfers. Model installation is explicit and separately documented.
Browser-relative routes are required for Arena preview; CORS is not authentication.

## 9. Open questions / delegated choices
The source specified endpoint names but not request/response/status shapes, bounds, job
semantics, preview timing workload or project persistence. This contract resolves these
under delegated architectural authority, including default PCM_24, model-offline policy,
asset handles rather than trusted absolute paths, and defined desktop viewport support.
No blocking API question. Real model runtime, measured latency and browser/audio behavior
remain verification obligations, not evidence created by this approved document.

## 10. Verification plan
Planned, not available in this documentation-only session:
- `.venv/bin/python -m pytest tests/app/test_api.py -v` (AC-1–7, AC-12).
- `npm --prefix frontend run test -- --run` (AC-8; Vitest).
- `npm --prefix frontend run test:e2e` (AC-9–11; Playwright).
- `npm --prefix frontend run lint` and `npm --prefix frontend run typecheck`.

| AC | Required test name | Planned file |
| --- | --- | --- |
| AC-1 | test_ac_1_project_schema | tests/app/test_api.py |
| AC-2 | test_ac_2_upload_and_peaks | tests/app/test_api.py |
| AC-3 | test_ac_3_demucs_modes | tests/app/test_api.py |
| AC-4 | test_ac_4_job_websocket | tests/app/test_api.py |
| AC-5 | test_ac_5_preview_slice | tests/app/test_api.py |
| AC-6 | test_ac_6_render_downloads | tests/app/test_api.py |
| AC-7 | test_ac_7_security_limits | tests/app/test_api.py |
| AC-8 | test_ac_8_history_persistence | frontend/tests/store.test.ts |
| AC-9 | test_ac_9_desktop_layout | frontend/tests/e2e/studio.spec.ts |
| AC-10 | test_ac_10_transport_regions | frontend/tests/e2e/studio.spec.ts |
| AC-11 | test_ac_11_accessibility_errors | frontend/tests/e2e/studio.spec.ts |
| AC-12 | test_ac_12_preview_latency | tests/app/test_api.py |

TS tests must use named function declarations `function test_ac_<n>_<slug>()` passed to
Vitest/Playwright so the current structural linter can recognize the names; actually
executing them remains mandatory. Fake-model tests cannot replace separately recorded
real-model smoke evidence when claiming separation works on deployed hardware.

## 11. Trace
Dependencies SPEC-001/SPEC-002/SPEC-003; PLAN-001 → T-004. Task paths are planned,
not existing product evidence. TRACE lists existing docs; product trace rows are populated
with actual paths only when the builder creates them.
