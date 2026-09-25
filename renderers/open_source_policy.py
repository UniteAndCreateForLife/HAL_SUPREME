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
    # Clean permissive video generators.
    "kandinsky-5-video-pro": ModelLicenseRecord(
        model_id="kandinsky-5-video-pro",
        role="high_quality_hd_text_image_to_video",
        code_license="MIT",
        weights_license="MIT",
        repository="https://github.com/kandinskylab/kandinsky-5",
        note="19B HD T2V/I2V lane; use on large-memory workers.",
    ),
    "kandinsky-5-video-lite": ModelLicenseRecord(
        model_id="kandinsky-5-video-lite",
        role="lightweight_text_image_to_video",
        code_license="MIT",
        weights_license="MIT",
        repository="https://github.com/kandinskylab/kandinsky-5",
        note="2B T2V/I2V lane; useful as a secondary local renderer.",
    ),
    "step-video-t2v": ModelLicenseRecord(
        model_id="step-video-t2v",
        role="large_text_to_video_fallback",
        code_license="MIT",
        weights_license="MIT",
        repository="https://github.com/stepfun-ai/Step-Video-T2V",
        note="30B/204-frame fallback for large-memory workers.",
    ),
    "wan2.2-ti2v-5b": ModelLicenseRecord(
        model_id="wan2.2-ti2v-5b",
        role="photoreal_text_image_to_video",
        code_license="Apache-2.0",
        weights_license="Apache-2.0",
        repository="https://github.com/Wan-Video/Wan2.2",
        note="Default local lane; quantized GGUF/offload variants can target low-VRAM workers.",
    ),
    "wan2.2-t2v-a14b": ModelLicenseRecord(
        model_id="wan2.2-t2v-a14b",
        role="high_quality_text_to_video",
        code_license="Apache-2.0",
        weights_license="Apache-2.0",
        repository="https://github.com/Wan-Video/Wan2.2",
    ),
    "wan2.2-i2v-a14b": ModelLicenseRecord(
        model_id="wan2.2-i2v-a14b",
        role="high_quality_image_to_video",
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

    # Music / authorized voice.
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

    # Frontier/open-weight candidates deliberately quarantined from strict mode.
    "magi-2-preview": ModelLicenseRecord(
        model_id="magi-2-preview",
        role="frontier_unified_audio_video_1080p",
        code_license="Apache-2.0",
        weights_license="Apache-2.0",
        repository="https://github.com/SandAI-org/MAGI-2-preview",
        enabled_in_strict_mode=False,
        note=(
            "Frontier candidate. Upstream package declares Apache-2.0, but the released "
            "checkpoint tree includes a Stable Audio Open component whose upstream model "
            "uses the Stability AI Community License. Keep quarantined until dependency "
            "license provenance is audited or the component is replaced."
        ),
    ),
    "minimax-h3": ModelLicenseRecord(
        model_id="minimax-h3",
        role="frontier_open_weight_audio_video",
        code_license="MiniMax-H3-Community",
        weights_license="MiniMax-H3-Community",
        repository="https://huggingface.co/MiniMaxAI/MiniMax-H3",
        enabled_in_strict_mode=False,
        note="Community license excludes the United States, EU, UK and South Korea.",
    ),
    "skyreels-v3": ModelLicenseRecord(
        model_id="skyreels-v3",
        role="reference_video_extension_talking_avatar",
        code_license="Skywork-Community",
        weights_license="Skywork-Community",
        repository="https://github.com/SkyworkAI/SkyReels-V3",
        enabled_in_strict_mode=False,
        note="Commercial-capable community license, but not OSI/permissive open source.",
    ),
    "hunyuan-video-1.5": ModelLicenseRecord(
        model_id="hunyuan-video-1.5",
        role="lightweight_high_quality_t2v_i2v",
        code_license="Tencent-Hunyuan-Community",
        weights_license="Tencent-Hunyuan-Community",
        repository="https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5",
        enabled_in_strict_mode=False,
        note="Tencent community license; not accepted by HAL strict-open-source profile.",
    ),
    "ltx-2": ModelLicenseRecord(
        model_id="ltx-2",
        role="audio_video_generation",
        code_license="LTX-2.x-Community",
        weights_license="LTX-2.x-Community",
        repository="https://github.com/Lightricks/LTX-2",
        enabled_in_strict_mode=False,
        note="Source-available/community license; not accepted by HAL strict-open-source profile.",
    ),
    "ltx-2.5": ModelLicenseRecord(
        model_id="ltx-2.5",
        role="audio_video_generation",
        code_license="LTX-Community",
        weights_license="LTX-Community",
        repository="https://github.com/Lightricks/LTX-2",
        enabled_in_strict_mode=False,
        note="Open weights but community license; not accepted by HAL strict-open-source profile.",
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
