# SPEC-001 SPEC-002 SPEC-003 SPEC-004
from __future__ import annotations

import copy
import io
import threading
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np
import soundfile as sf

from ..dsp.engine import DSPError, canonicalize, mix_tracks, render_track
from ..dsp.filters import Audio
from ..dsp.mastering import MasterResult, master
from ..dsp.regions import apply_regions
from .schemas import Project, Track


def uid() -> str:
    return uuid4().hex


@dataclass
class Asset:
    id: str
    project_id: str
    path: Path
    audio: Audio


class Workspace:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.assets: dict[str, Asset] = {}
        self.projects: dict[str, Project] = {}
        self.heavy = threading.Lock()
        self.cache: OrderedDict[str, MasterResult] = OrderedDict()

    def asset(self, id: str, project_id: str | None = None) -> Asset:
        a = self.assets.get(id)
        if not a or (project_id is not None and a.project_id != project_id):
            raise DSPError("asset_not_found")
        if a.path.is_symlink() or not a.path.resolve().is_relative_to(self.root):
            raise DSPError("asset_not_found")
        return a

    def add(self, audio: Audio, project_id: str) -> Asset:
        id = uid()
        path = self.root / f"{id}.wav"
        sf.write(path, audio, 48000, subtype="FLOAT")
        a = Asset(id, project_id, path, audio.copy())
        self.assets[id] = a
        return a

    def ingest(self, raw: bytes, project_id: str | None) -> dict[str, Any]:
        if project_id is not None and project_id not in self.projects:
            raise DSPError("project_not_found")
        project = (
            self.projects[project_id].model_copy(deep=True)
            if project_id
            else Project(project_id=uid())
        )
        if len(project.tracks) >= 8:
            raise DSPError("project_limit")
        try:
            info = sf.info(io.BytesIO(raw))
            if info.format not in ("WAV", "WAVEX", "FLAC", "AIFF") or info.channels not in (1, 2):
                raise DSPError("unsupported_audio")
            if info.duration > 1800:
                raise DSPError("duration_limit")
            x, rate = sf.read(io.BytesIO(raw), dtype="float32", always_2d=True)
            x = canonicalize(x, rate)
        except (RuntimeError, ValueError) as exc:
            if isinstance(exc, DSPError):
                raise
            raise DSPError("unsupported_audio") from exc
        a = self.add(x, project.project_id)
        (self.root / f"{a.id}.original").write_bytes(raw)
        project.tracks.append(
            Track(track_id=uid(), name=f"Track {len(project.tracks) + 1}", file_path=a.id)
        )
        self.projects[project.project_id] = project
        peaks = []
        for channel in range(2):
            bins = np.array_split(x[:, channel], 512)
            peaks.append([[float(b.min()), float(b.max())] if len(b) else [0.0, 0.0] for b in bins])
        return dict(
            asset_id=a.id,
            file_path=a.id,
            duration_sec=len(x) / 48000,
            sample_rate=48000,
            channels=2,
            waveform_peaks=dict(bins=512, channels=peaks),
            project=project.model_dump(),
        )

    def validate(self, p: Project) -> None:
        if p.project_id not in self.projects:
            raise DSPError("project_not_found")
        maximum = 0.0
        for t in p.tracks:
            duration = len(self.asset(t.file_path, p.project_id).audio) / 48000
            maximum = max(maximum, duration)
            if any(r.end_sec > duration for r in t.regions):
                raise DSPError("invalid_region")
        if any(r.end_sec > maximum for r in p.master_bus.regions):
            raise DSPError("invalid_region")

    def render(self, p: Project, bypass_master: bool = False) -> MasterResult:
        self.validate(p)
        key = p.model_dump_json() + str(bypass_master)
        if key not in self.cache:
            settings = [t.model_dump() for t in p.tracks]
            buffers = [
                render_track(
                    self.asset(t.file_path, p.project_id).audio,
                    s,
                    lambda a, regions: apply_regions(a, regions, bpm=p.bpm).audio,
                )
                for t, s in zip(p.tracks, settings, strict=True)
            ]
            summed = mix_tracks(buffers, settings)
            bus = apply_regions(
                summed.audio, [r.model_dump() for r in p.master_bus.regions], bpm=p.bpm
            ).audio
            if bypass_master:
                result = MasterResult(bus, {}, p.master_bus.target_lufs)
            else:
                result = master(bus, p.master_bus.model_dump())
                result.telemetry["pre_master_gain_db"] = summed.pre_master_gain_db
            self.cache[key] = result
            while len(self.cache) > 8:
                self.cache.popitem(last=False)
        cached = self.cache[key]
        self.cache.move_to_end(key)
        return MasterResult(cached.audio, copy.deepcopy(cached.telemetry), cached.target_lufs)
