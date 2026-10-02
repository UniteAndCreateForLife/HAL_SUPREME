from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Literal

from .open_source_policy import validate_strict_open_source_profile


ShotLane = Literal["world", "performance", "gesture", "longform_sync"]


@dataclass(frozen=True)
class LongFormProductionProfile:
    duration_seconds: float = 360.0
    width: int = 1920
    height: int = 1080
    fps: float = 24.0
    audio_sample_rate: int = 48000
    shot_target_seconds: float = 5.0
    strict_open_source: bool = True

    world_model: str = "wan2.2-ti2v-5b"
    performance_model: str = "wan2.2-s2v-14b"
    gesture_model: str = "wan2.2-animate-14b"
    longform_sync_model: str = "infinitetalk"
    music_model: str = "ace-step-1.5-xl-sft"
    music_fallback_model: str = "heartmula-oss-3b-happy-new-year"
    authorized_voice_model: str = "seed-vc"

    def model_ids(self) -> tuple[str, ...]:
        return (
            self.world_model,
            self.performance_model,
            self.gesture_model,
            self.longform_sync_model,
            self.music_model,
            self.music_fallback_model,
            self.authorized_voice_model,
        )

    def validate(self) -> None:
        if self.duration_seconds < 60:
            raise ValueError("Nightmare Studio long-form profile requires at least 60 seconds")
        if self.width < 1280 or self.height < 720:
            raise ValueError("long-form master must be at least 1280x720")
        if self.fps < 23.0:
            raise ValueError("production fps must be at least 23")
        if not 3.0 <= self.shot_target_seconds <= 8.0:
            raise ValueError("shot_target_seconds must stay between 3 and 8 seconds")
        if self.strict_open_source:
            validate_strict_open_source_profile(self.model_ids())


@dataclass(frozen=True)
class ShotPlan:
    index: int
    start_seconds: float
    end_seconds: float
    lane: ShotLane
    model_id: str

    @property
    def duration_seconds(self) -> float:
        return self.end_seconds - self.start_seconds


@dataclass(frozen=True)
class MusicSectionPlan:
    index: int
    start_seconds: float
    end_seconds: float
    mode: Literal["generate", "complete", "repaint_bridge"]

    @property
    def duration_seconds(self) -> float:
        return self.end_seconds - self.start_seconds


@dataclass(frozen=True)
class LongFormPlan:
    profile: LongFormProductionProfile
    shots: tuple[ShotPlan, ...]
    music_sections: tuple[MusicSectionPlan, ...]


def _lane_for(index: int) -> ShotLane:
    # Deterministic cadence: environment/world coverage is the base layer,
    # while audio-driven and gesture-controlled shots recur frequently enough
    # to keep human performance visibly alive.
    if index % 11 == 0:
        return "longform_sync"
    if index % 7 == 0:
        return "gesture"
    if index % 4 == 0:
        return "performance"
    return "world"


def _model_for(profile: LongFormProductionProfile, lane: ShotLane) -> str:
    return {
        "world": profile.world_model,
        "performance": profile.performance_model,
        "gesture": profile.gesture_model,
        "longform_sync": profile.longform_sync_model,
    }[lane]


def plan_long_form(profile: LongFormProductionProfile) -> LongFormPlan:
    profile.validate()

    shot_count = max(1, ceil(profile.duration_seconds / profile.shot_target_seconds))
    shot_duration = profile.duration_seconds / shot_count

    shots = []
    for index in range(shot_count):
        start = index * shot_duration
        end = profile.duration_seconds if index == shot_count - 1 else (index + 1) * shot_duration
        lane = _lane_for(index)
        shots.append(
            ShotPlan(
                index=index,
                start_seconds=start,
                end_seconds=end,
                lane=lane,
                model_id=_model_for(profile, lane),
            )
        )

    # ACE-Step can target long durations, but its own guide describes 2-4 minute
    # generations as the stable range. For longer masters, plan continuity in
    # bounded musical sections so completion/repaint can preserve structure.
    stable_music_section = 180.0
    music_count = max(1, ceil(profile.duration_seconds / stable_music_section))
    music_sections = []
    for index in range(music_count):
        start = index * stable_music_section
        end = min(profile.duration_seconds, (index + 1) * stable_music_section)
        mode = "generate" if index == 0 else ("repaint_bridge" if index % 2 == 0 else "complete")
        music_sections.append(
            MusicSectionPlan(
                index=index,
                start_seconds=start,
                end_seconds=end,
                mode=mode,
            )
        )

    return LongFormPlan(profile=profile, shots=tuple(shots), music_sections=tuple(music_sections))
