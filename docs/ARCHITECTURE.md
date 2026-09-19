# HAL SUPREME Architecture

## Control plane
The stable core owns identity, authorization, WorkGraph state, checkpoints, artifact provenance, QC and release decisions.

## Replaceable worker plane
GPU and external workers provide capabilities such as voice synthesis, segmentation, depth estimation and moving-world generation. A worker result is staged, verified and then committed; provider success alone is never equivalent to HAL acceptance.

## Renderer boundary
DreamForge requests a capability rather than a vendor. Renderer adapters declare capabilities and health. Initial renderer targets are:
1. ComfyUI / Wan-class moving-world generation
2. LTX-class video generation
3. Reality Stage deterministic continuous-motion fallback

Each accepted render must emit an artifact plus provenance and temporal-motion evidence.

## Resume integrity
Recovery reconstructs state from durable receipts, not worker memory. Verified artifacts are reused by hash. Missing identity, voice authorization, model provenance, or required motion evidence blocks release.

## Security
Credentials remain outside Git. Configuration committed to this repository must be templates or non-secret defaults.
