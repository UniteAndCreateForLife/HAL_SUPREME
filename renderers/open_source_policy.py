from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


OSI_PERMISSIVE_OR_COPYLEFT = frozenset(
    {
        "Apache-2.0",
        "MIT",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "GPL-3.0",
        "AGPL-3.0",
        "LGPL-3.0",
    }
)


@dataclass(frozen=True)
class ModelLicenseRecord:
    model_id: str
    role: str
    code_license: str
    weights_license: str
    repository: str
    enabled_in_strict_mode: bool = True
    note: str = ""

    @property
    def is_strict_open_source(self) -> bool:
        return (
            self.enabled_in_strict_mode
            and self.code_license in OSI_PERMISSIVE_OR_COPYLEFT
            and self.weights_license in OSI_PERMISSIVE_OR_COPYLEFT
        )


MODEL_LICENSES: dict[str, ModelLicenseRecord] = {
    "wan2.2-ti2v-5b": ModelLicenseRecord(
        model_id="wan2.2-ti2v-5b",
        role="photoreal_text_image_to_video",
        code_license="Apache-2.0",
        weights_license="Apache-2.0",
        repository="https://github.com/Wan-Video/Wan2.2",
    ),
    "wan2.2-s2v-14b": ModelLicenseRecord(
        model_id="wan2.2-s2v-14b",
        role="audio_driven_cinematic_performance",
        code_license="Apache-2.0",
        weights_license="Apache-2.0",
        repository="https://github.com/Wan-Video/Wan2.2",
    ),
    "wan2.2-animate-14b": ModelLicenseRecord(
        model_id="wan2.2-animate-14b",
        role="gesture_expression_character_animation",
        code_license="Apache-2.0",
        weights_license="Apache-2.0",
        repository="https://github.com/Wan-Video/Wan2.2",
    ),
    "infinitetalk": ModelLicenseRecord(
        model_id="infinitetalk",
        role="long_form_audio_driven_face_and_body_video",
        code_license="Apache-2.0",
        weights_license="Apache-2.0",
        repository="https://github.com/MeiGen-AI/InfiniteTalk",
    ),
    "multitalk": ModelLicenseRecord(
        model_id="multitalk",
        role="multi_person_audio_driven_performance",
        code_license="Apache-2.0",
        weights_license="Apache-2.0",
        repository="https://github.com/MeiGen-AI/MultiTalk",
    ),
    "ace-step-1.5-xl-sft": ModelLicenseRecord(
        model_id="ace-step-1.5-xl-sft",
        role="full_song_music_and_vocals",
        code_license="MIT",
        weights_license="MIT",
        repository="https://github.com/ace-step/ACE-Step-1.5",
    ),
    "heartmula-oss-3b-happy-new-year": ModelLicenseRecord(
        model_id="heartmula-oss-3b-happy-new-year",
        role="alternate_full_song_music_and_vocals",
        code_license="Apache-2.0",
        weights_license="Apache-2.0",
        repository="https://github.com/HeartMuLa/heartlib",
    ),
    "seed-vc": ModelLicenseRecord(
        model_id="seed-vc",
        role="authorized_self_voice_singing_conversion",
        code_license="GPL-3.0",
        weights_license="GPL-3.0",
        repository="https://github.com/Plachtaa/seed-vc",
        note="Use only with an authorized/enrolled voice identity.",
    ),
    # Deliberately tracked but blocked in strict mode.
    "ltx-2": ModelLicenseRecord(
        model_id="ltx-2",
        role="audio_video_generation",
        code_license="LTX-2.x-Community",
        weights_license="LTX-2.x-Community",
        repository="https://github.com/Lightricks/LTX-2",
        enabled_in_strict_mode=False,
        note="Source-available/community license; not accepted by HAL strict-open-source profile.",
    ),
    "mmaudio": ModelLicenseRecord(
        model_id="mmaudio",
        role="video_to_audio",
        code_license="MIT",
        weights_license="CC-BY-NC-4.0",
        repository="https://github.com/SonyResearch/MMAudio",
        enabled_in_strict_mode=False,
        note="Checkpoint license is non-commercial; blocked for strict reusable production.",
    ),
}


def require_strict_open_source(model_id: str) -> ModelLicenseRecord:
    try:
        record = MODEL_LICENSES[model_id]
    except KeyError as exc:
        raise KeyError(f"unreviewed model: {model_id}") from exc
    if not record.is_strict_open_source:
        raise ValueError(
            f"model {model_id!r} is not allowed in strict-open-source mode: "
            f"code={record.code_license}, weights={record.weights_license}, "
            f"enabled={record.enabled_in_strict_mode}"
        )
    return record


def validate_strict_open_source_profile(model_ids: Iterable[str]) -> tuple[ModelLicenseRecord, ...]:
    return tuple(require_strict_open_source(model_id) for model_id in model_ids)
