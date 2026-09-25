# Persistent Cinematic World Engine

HAL should make a film by photographing a persistent world, not by asking unrelated video jobs to invent adjacent shots.

## Architectural rule

The cinematic world is a rebuildable projection of HAL state, not a new authority. EventStore remains canonical history, WorkGraph remains work state, Supervisor remains process authority, ProviderMesh remains provider routing, and Godot remains the deterministic performance stage. Generative workers may propose or enhance pixels, geometry, texture, motion, sound, and lighting; they do not silently redefine identity or world state.

The versioned `hal.cinematic-world/v1` manifest binds stable asset IDs, entity IDs, scene anchors, continuity segments, shot inheritance, and explicit state transitions. A shot receives a deterministic continuity fingerprint before rendering. A provider job that cannot prove which fingerprint it rendered is not continuity-safe production evidence.

## Persistent asset pipeline

Images and footage become reusable assets before they become finished shots. Character references are reconstructed and rigged into a versioned canonical character; wardrobe is registered separately so clothing changes are intentional. Props become PBR meshes or splats with stable IDs. Locations are reconstructed into a spatial set with persistent camera scale, anchors, collision/affordance metadata, and lighting references. Every accepted asset carries lineage and, when materialized, a content hash.

### Photoreal environment rule

A box-model corridor is a **blockout**, never a final visible set. Production environments that declare `photoreal_from_capture` must be reconstructed from multi-image, video, or photogrammetry input. The manifest records the source capture, visual representation, visual artifact, separate collision artifact, and whether geometry is measured/reconstructed versus merely inferred.

HAL uses a hybrid environment package:

- **visual shell:** Gaussian splat, high-resolution textured mesh, or both, reconstructed from the approved images/video;
- **simulation shell:** clean low-complexity mesh used invisibly for collision, navigation, anchors, ray tests, occlusion and physics;
- **live semantic surfaces:** mirrors, windows, screens, doors, water and other elements that must respond to moving performers or lighting are explicit Godot entities instead of being baked permanently into the capture;
- **dynamic objects:** characters and interactive props remain rigged/PBR assets with stable IDs and transforms;
- **camera/control passes:** depth, normals, entity IDs, pose, camera matrices and motion are exported from the deterministic stage for neural finishing.

This preserves the photographic appearance of a captured location without sacrificing game-engine control. A splat can provide the highest-fidelity static appearance while its invisible proxy mesh provides physical interaction; when relighting or deformation is important, a textured/PBR mesh or hybrid representation is preferred.

Single-image world generation is useful for ideation and fictional spaces, but hidden geometry is necessarily inferred. It must not be labeled capture-faithful production geometry unless additional views or measured reconstruction evidence resolve the unseen space.

OpenUSD is the preferred interchange/composition layer for complex scene graphs, variants, references, payloads, cameras, lights, skeletons and non-destructive overrides. Godot remains the bounded live stage. Blender is an authoring/repair surface, and Unreal can be an optional USD review/virtual-production surface; neither becomes HAL's factual authority.

## Shot compiler

A shot compiler resolves a WorkGraph shot intent into one exact world state:

`EventStore snapshot -> WorldManifest -> asset/scene resolution -> actor placement -> camera/light/performance state -> deterministic stage passes -> neural enhancement -> continuity audit -> motion/provenance QC -> accepted artifact`

The stage should emit more than a beauty frame. Useful control passes include depth, normals, entity/segmentation IDs, skeleton/pose, optical flow or motion vectors, camera intrinsics/extrinsics, material/object IDs, and lighting metadata. Neural video then receives these controls plus the canonical references instead of being allowed to re-invent the world.

## Continuity gate

Continuity has two layers. The deterministic preflight checks the manifest: stable character identity, wardrobe, set geometry, persistent props, anchors, shot ordering, and declared transitions. The post-render audit checks the actual pixels against those expectations. Required visual domains are identity, wardrobe, set geometry, props, lighting and atmosphere. Missing or low-confidence evidence fails closed.

Malformed outputs are valuable as negative evaluation data. A clip that changes a corridor into another room, changes a shirt, drops a prop, invents daylight, or mutates a face should be tagged with the failed domains and retained in the LAB/GRAVEYARD evaluation corpus, not edited into the film.

## Current reconstruction adapters to evaluate

- **World Labs Marble / World API:** image, multi-image and video-to-world reconstruction/generation with exportable Gaussian splats and meshes. Treat as a replaceable remote world worker.
- **World Labs Atlas:** early-access higher-end world model for spatial reconstruction and camera-controlled generation; evaluate when access is available, never make it a required authority.
- **HY-World 2.x / WorldMirror 2.x:** open-source multi-view or video reconstruction into persistent 3D representations, useful for locations and world capture.
- **VGGT + COLMAP/gsplat:** open geometry bootstrap for camera intrinsics/extrinsics, depth, point maps and tracks, followed by Gaussian-splat optimization when full world-model compute is unavailable.
- **TRELLIS.2:** image-to-PBR 3D/GLB for reusable objects and many wardrobe/prop assets.
- **SAM 3D Objects:** real-image object reconstruction and multi-object scene extraction; useful for object discovery and initial spatial alignment.
- **SAM 3D Body / MetaHuman-style fitting:** human body/head reconstruction candidates for canonical characters, followed by our own rig/identity validation.
- **Blender + OpenUSD:** asset repair, rigging, material work, geometry cleanup and DCC interchange.
- **Godot:** persistent deterministic simulation/performance stage and source of control passes.
- **Unreal USD Stage (optional):** high-end USD inspection, lighting/look-development and virtual-production experiments without changing authority.
- **LTX/Wan/other neural video:** finishing/enhancement workers conditioned by references and stage controls; never the source of identity or scene truth.

Model licenses and hardware requirements must be checked per adapter before production deployment. ProviderMesh should select reconstruction/render workers by capability and evidence, not hard-code one vendor.

## HAL as director

HAL's cognition should operate above the stage: choose dramatic intent, blocking, lens language, performance beats, atmosphere and edits; compile them into typed WorkGraph work; observe resulting evidence through HAL Eye; critique; then approve, revise or reject. Agents and MCP tools can contribute specialized proposals, but all durable changes return through the same EventStore/WorkGraph path.

This lets the system accumulate a real studio: one character improves over many films; a room gains more props and better materials; lights and camera rigs become reusable; motion clips, facial performances and sound spaces become assets; and every production makes the simulation richer instead of discarding everything at the end of each generated clip.

## Preview acceptance target

Do not make the next preview by stitching unrelated text/image-to-video generations. First register one canonical hero, one canonical set, wardrobe, a small prop inventory, camera/light presets and a short performance plan. Then make a continuous 30-60 second pilot from the same staged world, with multiple camera setups but explicit continuity inheritance. Neural enhancement is optional per shot; identity/set/prop continuity is mandatory.
