# SPEC-004
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class Region(Model):
    region_id: str = Field(min_length=1, max_length=128)
    start_sec: float = Field(ge=0)
    end_sec: float = Field(gt=0)
    effect_type: Literal[
        "HARD_MUTE",
        "NASA_WALKIE_TALKIE",
        "UNDERWATER_WOMB",
        "ANALOG_TAPE_STOP",
        "TAPE_STUTTER_DEGRADE",
        "SUB_40HZ_DROP",
    ]
    wet_mix: float = Field(default=1, ge=0, le=1)
    fade_ms: float = Field(default=8, ge=2, le=15)

    @model_validator(mode="after")
    def timing(self) -> Region:
        if round(self.end_sec * 48000) - round(self.start_sec * 48000) < 2:
            raise ValueError("invalid region bounds")
        return self


class Strip(Model):
    hp_hz: float = Field(default=20, ge=20, le=500)
    de_mud_db: float = Field(default=-2, ge=-6, le=3)
    presence_db: float = Field(default=0, ge=-6, le=6)
    de_fizz_db: float = Field(default=-1.8, ge=-6, le=0)
    comp_threshold_db: float = Field(default=-18, ge=-40, le=0)
    comp_ratio: float = Field(default=4, ge=1, le=10)
    comp_attack_ms: float = Field(default=25, ge=1, le=100)
    comp_release_ms: float = Field(default=120, ge=20, le=500)


class Track(Model):
    track_id: str = Field(min_length=1, max_length=128)
    name: str = Field(default="Track", max_length=256)
    file_path: str = Field(min_length=1, max_length=128)
    gain_db: float = Field(default=0, ge=-24, le=12)
    pan: float = Field(default=0, ge=-1, le=1)
    mute: bool = False
    solo: bool = False
    phase_invert: bool = False
    channel_strip: Strip = Field(default_factory=Strip)
    regions: list[Region] = Field(default_factory=list, max_length=128)

    @model_validator(mode="after")
    def unique_regions(self) -> Track:
        if len({r.region_id for r in self.regions}) != len(self.regions):
            raise ValueError("duplicate region id")
        return self


Gain = Annotated[float, Field(ge=-12, le=12)]


class MasterBus(Model):
    mono_bass_cutoff_hz: float = Field(default=85.0, ge=85, le=85)
    stereo_width: float = Field(default=1.15, ge=0, le=1.5)
    pultec_low_boost_db: Gain = 2.2
    mud_cut_db: Gain = -2.5
    mid_bite_db: Gain = 1.8
    air_boost_db: Gain = 1.6
    parallel_comp_mix: float = Field(default=0.18, ge=0, le=1)
    tape_drive: float = Field(default=1.22, ge=1, le=2)
    target_lufs: float = Field(default=-9.5, ge=-14, le=-8)
    ceiling_db: float = Field(default=-0.3, ge=-0.3, le=-0.3)
    regions: list[Region] = Field(default_factory=list, max_length=128)

    @model_validator(mode="after")
    def unique_regions(self) -> MasterBus:
        if self.target_lufs not in (-14, -9.5, -8):
            raise ValueError("invalid target LUFS")
        if len({r.region_id for r in self.regions}) != len(self.regions):
            raise ValueError("duplicate region id")
        return self


class Project(Model):
    project_id: str = Field(min_length=1, max_length=128)
    sample_rate: Literal[48000] = 48000
    master_bus: MasterBus = Field(default_factory=MasterBus)
    bpm: float | None = Field(default=None, gt=0)
    tracks: list[Track] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def unique_tracks(self) -> Project:
        if len({t.track_id for t in self.tracks}) != len(self.tracks):
            raise ValueError("duplicate track id")
        return self


class RenderRequest(Project):
    export_bit_depth: Literal[16, 24] = 24


class Preview(Model):
    project: Project
    target_type: Literal["track", "master"]
    track_id: str | None = None
    region_id: str
    bypass_master: bool = False


class Split(Model):
    project_id: str
    track_id: str
    mode: Literal["2stem", "4stem"]
