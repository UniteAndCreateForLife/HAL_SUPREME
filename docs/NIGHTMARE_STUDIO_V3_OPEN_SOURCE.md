# Nightmare Studio v3 — Strict Open-Source Long-Form Production

Status: implementation target for HAL SUPREME
Verified model/license research date: 2026-09-21

## Objective

Upgrade the existing 48-second Nightmare Studio prototype into a local-first production system for approximately 4-6 minute music videos with genuine temporal motion, realistic human performance, reusable 3D assets, full songs with vocals, and deterministic QC.

The strict profile prohibits paid generation APIs and also prohibits weights whose licenses are merely source-available, community-only, or non-commercial.

## Default open stack

### Music and vocals

1. ACE-Step 1.5 XL SFT — primary full-song generator.
   - MIT project license.
   - Supports lyrics, vocals, reference audio, remix, repaint, complete/extension workflows, BPM/key/time-signature metadata, and long target durations.
   - Treat 2-4 minute generations as the stable unit. Longer masters should be assembled with Complete/Repaint continuity rather than relying on a single monolithic generation.

2. HeartMuLa OSS 3B Happy New Year + HeartCodec — A/B fallback.
   - Apache-2.0 code and public model weights.
   - Use for alternate lyric delivery, arrangement candidates, or recovery when ACE-Step is unavailable.

3. Seed-VC — authorized self-voice conversion lane.
   - GPL-3.0.
   - Supports zero-shot speech and singing voice conversion from a short reference, plus fine-tuning.
   - This lane must remain behind HAL's voice authorization/provenance gate.

## Video and performance

1. Wan2.2 TI2V 5B — primary photoreal world/shot generator.
   - Apache-2.0 repository/model family.
   - 720p/24fps consumer-GPU-oriented base lane; upscale/master later rather than fabricating still-frame motion.

2. Wan2.2 S2V 14B — audio-driven cinematic performance lane.
   - Use on vocal/performance shots where mouth, face, body, and scene response must follow audio.

3. Wan2.2 Animate 14B — gesture/expression and character replacement lane.
   - Use recorded or canonical motion references to preserve believable body mechanics and facial expression.

4. InfiniteTalk — long-form audio-driven video lane.
   - Apache-2.0.
   - Use when performance continuity must run longer than a normal generative shot.

5. MultiTalk — multi-person singing/conversation lane.
   - Apache-2.0.
   - Use only when a shot contains multiple independently driven performers.

## Reusable 3D continuity layer

Generative video is not the sole source of geometry. Blender and Godot remain the deterministic continuity layer for canonical characters, sets, props, instruments, cameras, lighting rigs, materials, masks, depth references, and motion blocking.

The rule is: manufacture reusable assets and rigs once, then render new shots from them. Do not treat a previously flattened MP4 as the reusable asset.

## Long-form construction

Default master target:
- 360 seconds
- 1920x1080 delivery
- 24 fps
- 48 kHz audio
- approximately 5-second generative shot units

A six-minute master therefore contains roughly 72 independently verifiable moving shots. HAL can re-render one failed shot without invalidating the other 71.

Music is planned in <=180-second stable sections. The first section is generated normally; later sections use completion/repaint logic to preserve key, vocal identity, arrangement vocabulary, and transitions. The final master is assembled only after loudness, true-peak, decode, duration, motion, sync, and hash verification.

## Sound design

The target is original dark midtempo bass / IDM / glitch production, not direct imitation of a named living artist. Sound design should emphasize:
- sub-bass fundamentals and controlled harmonics
- asymmetrical glitch percussion
- granular vocal fragments
- industrial/transient impacts
- synthetic choir or spectral pads
- instrument gestures tied to visible movement
- intentional silence and dynamic contrast
- multi-band sidechain and transient control

Where strict licensing matters, prefer generated material, procedural synthesis, user-owned recordings, and CC0/appropriately licensed foley. Do not silently import non-commercial checkpoints or copyrighted reference audio.

## License gate

`renderers/open_source_policy.py` is authoritative for the strict profile.

Currently blocked by design:
- LTX-2: current LTX-2.x model family uses a Lightricks Community License rather than an OSI-style permissive/copyleft model license.
- MMAudio checkpoints: code is MIT but published checkpoints are CC-BY-NC-4.0, so they are not suitable for a strict reusable/commercial production profile.

A new model is not allowed merely because its GitHub repository is public. HAL requires both code and the actual weights used for rendering to pass the license gate.

## Quality bar

"Commercial-model quality" is an engineering target, not a claim. No open model should be labeled "Suno 6 quality" or "feature-film quality" without an actual A/B evaluation.

Nightmare Studio v3 should improve quality through ensemble production:
1. generate multiple music candidates;
2. select by measurable audio QC plus human review;
3. use dedicated performance/gesture lanes instead of text-to-video for every shot;
4. keep persistent characters and sets;
5. re-render only rejected shots;
6. master at the end rather than overprocessing each generation;
7. record exact models, hashes, seeds, prompts, references, and licenses in the handoff receipt.

## Required v3 release gates

A release is accepted only when:
- every active model passes strict-open-source policy;
- the full MP4 decodes;
- video contains temporal motion rather than still duplication;
- audio is present for the full intended program;
- duration and dimensions match the project contract;
- voice identity, when used, has an authorization receipt;
- each shot has provenance and its source assets can be traced;
- the final artifact has SHA-256;
- no paid API call or public upload occurred unless separately authorized.
