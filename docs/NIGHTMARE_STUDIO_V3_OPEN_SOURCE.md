# Nightmare Studio v3 — Open Video Frontier Fabric

Status: active implementation target for HAL SUPREME
Research refresh: 2026-09-21

## Goal

Build the strongest practical open video production system available to HAL rather than treating one foundation model as the entire studio.

"Better than Sora" is a system-level target. Current public preference measurements show that newer models can outrank Sora 2 on particular leaderboards, but the highest-ranked open-weight candidates do not all have licenses or hardware requirements compatible with HAL. The strict production profile therefore separates:

1. clean permissive production models;
2. local low-VRAM execution;
3. large-GPU hero-shot execution; and
4. frontier candidates that remain quarantined until their full dependency/license chain is acceptable.

## Strict production stack

### World and cinematic generation

**Kandinsky 5 Video Pro**
- MIT.
- 19B HD text-to-video and image-to-video lane.
- Default high-memory hero/world renderer.

**Kandinsky 5 Video Lite**
- MIT.
- 2B lightweight T2V/I2V lane.
- Secondary renderer where memory is constrained.

**Wan2.2**
- Apache-2.0.
- TI2V-5B is the main low-VRAM-compatible world lane after quantization/offload.
- T2V-A14B / I2V-A14B are higher-capacity specialist lanes.
- S2V-14B is the audio-driven performance lane.
- Animate-14B is the gesture/expression/character-animation lane.

**Step-Video-T2V**
- MIT.
- Large 30B fallback for high-memory workers.
- Not a local 8 GB model.

### Long performance and character continuity

**InfiniteTalk**
- Apache-2.0.
- Long-form audio-driven face/body performance.

**MultiTalk**
- Apache-2.0.
- Multi-person audio-driven sequences.

**Blender + Godot**
- Persistent characters, sets, props, instruments, geometry, rigs, cameras, materials, lights and motion blocking.
- Generative outputs are new shots; flattened old video is not treated as the reusable asset.

## Local 8 GB HAL lane

HAL's low-VRAM worker does not pretend full-precision frontier models fit into GPU memory.

The local route is:

WAN TI2V-5B quantized -> LightX2V / ComfyUI-GGUF -> block/phase CPU offload -> short 480p/720p verified shots -> temporal QC -> upscale/interpolation -> 1080p/24 master.

Rules:
- one heavy video job at a time;
- prefer Q4/Q5-class Wan TI2V-5B for ordinary shots;
- use distilled/few-step Wan pipelines where compatible;
- use host RAM for offload;
- use the persistent 3D stage to manufacture composition, pose, identity and camera references;
- invoke S2V/Animate/InfiniteTalk only for shots that actually need those specialist capabilities.

This route optimizes usable final quality per byte of VRAM instead of selecting a model from leaderboard rank alone.

## Large-GPU lane

When a >=48 GB worker is available:
- Kandinsky 5 Video Pro becomes the primary world/hero renderer.
- Wan2.2 A14B remains available for alternate candidates.
- Wan2.2 S2V/Animate remain the performance specialists.
- InfiniteTalk remains the long-sync specialist.
- render multiple candidates for hero shots and select by QC/human review.

On a frontier cluster, Step-Video-T2V is added as another permissive candidate.

## Frontier candidates under quarantine

### MAGI-2 Preview

MAGI-2 Preview is a major frontier candidate: unified audio/video generation, 1080p refinement, 114B MoE architecture and very strong current public preference results.

Its repository declares Apache-2.0, but the released checkpoint package contains a Stable Audio Open component whose upstream model uses the Stability AI Community License. HAL therefore does not call the complete released package strictly permissive until the dependency is license-audited or replaced.

It is also far outside the local-machine envelope: the official configuration is hundreds of gigabytes and targets an eight-Hopper-GPU cluster.

### MiniMax H3

The public model is high-performing, but its current community license excludes deployment in the United States and several other regions. It is therefore disabled for this HAL deployment.

### SkyReels V3, HunyuanVideo 1.5, LTX-2.x

These are useful open-weight/source-available systems, but their current model terms are community licenses rather than HAL's strict permissive/copyleft profile. They remain optional research lanes, not strict production dependencies.

### MMAudio

The code is MIT but released checkpoints are non-commercial. It remains blocked.

## Audio/music stack

- ACE-Step 1.5 XL SFT: primary MIT full-song/vocal engine.
- HeartMuLa OSS 3B + HeartCodec: Apache-2.0 alternate.
- Seed-VC: GPL-3.0 authorized self-voice singing conversion.
- 48 kHz final master.
- Original generated/procedural/user-owned or appropriately licensed foley and samples.

## Six-minute construction

Default master:
- 360 seconds
- 1920x1080 delivery
- 24 fps
- 48 kHz audio
- ~5 second independently accepted shot units

Approximately 72 shot units make one six-minute film. Failed shots are replaced individually rather than forcing a complete regeneration.

The music master is created first. HAL then derives:
- section boundaries;
- beat/transient map;
- vocal phrase map;
- intensity curve;
- gesture cues;
- camera/edit cues.

Every video renderer receives the same authoritative timeline.

## Quality strategy

A single model is not expected to win every shot type.

HAL should outperform a single-model workflow through:
- persistent 3D identity and world continuity;
- model routing by shot purpose;
- multiple candidate generation for important shots;
- audio-driven face/body performance;
- deterministic beat/gesture linkage;
- shot-level motion and decode QC;
- continuity-aware edit selection;
- temporal interpolation and restoration only after genuine motion exists;
- final audio/video mastering after assembly.

No benchmark claim is promoted to "better than Sora" unless HAL itself passes an A/B evaluation on the same prompts, duration, resolution and human-review procedure.

## Release gates

A production cannot be marked accepted unless:
- all strict-profile code and weight licenses pass;
- dependency licenses are traced;
- every shot has model/seed/prompt/reference provenance;
- real temporal motion is measured;
- full MP4 decode passes;
- intended duration, frame rate and resolution match;
- audio spans the intended program;
- authorized voice use has an authorization receipt;
- final master receives a SHA-256;
- no paid API or public upload was used without explicit authorization.
