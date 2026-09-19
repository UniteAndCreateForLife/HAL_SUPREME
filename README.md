# HAL SUPREME

Canonical, curated source repository for HAL SUPREME.

HAL SUPREME is organized as a durable multimodal agent and production system. Stable control-plane state remains separate from replaceable AI workers and render backends.

## Architectural invariants
- Work is committed only after verification.
- Character/family identity is persistent and backend-independent.
- Authorized voice identity fails closed; generic TTS must never impersonate an enrolled human.
- Render providers are replaceable workers, never authorities over identity or release state.
- Every production stage is checkpointable and resumable.
- Delivered video must contain legitimate temporal motion; still-frame cheats fail QC.
- Artifacts carry provenance from inputs through verification and release.
- Secrets, model weights, caches, generated media, local databases and machine-specific state do not belong in Git.

## Production graph
INGEST → VOICE → SEGMENT → DEPTH → WORLD → COMPOSITE → RELIGHT → AUDIO_SPACE → GRADE → QC → MASTER

## Repository map
- core/ — stable runtime primitives
- workgraph/ — durable jobs, leases, attempts and checkpoints
- provider_mesh/ — capability routing and worker health
- manifest/ — production graph orchestration
- dreamforge/ — episode/shot compiler and renderer routing
- reality_stage/ — deterministic embodied/world stage
- renderers/ — replaceable render adapters
- voice/ — authorized voice routing and provenance
- vision/ — segmentation/depth/tracking adapters
- family/ — persistent character identity contracts
- provenance/ — artifact/operation receipts
- qc/ — acceptance gates
- services/ — service entrypoints
- integrations/ — external adapters
- schemas/ — versioned contracts
- configs/ — safe configuration templates
- scripts/ — operator/developer tools
- tests/ — contract, recovery and adversarial tests
- docs/ — architecture and runbooks
- deploy/ — deployment manifests

This repository starts clean by design. Existing HAL code is migrated only after review, rather than bulk-importing historical filesystem debris.
