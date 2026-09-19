# Renderer Fabric

Renderers are replaceable capability workers behind DreamForge.

A renderer adapter must report:
- provider/backend identity
- model and version
- health
- text-to-video / image-to-video / video-to-video support
- reference/identity conditioning support
- control-video support
- resolution, FPS and frame limits
- estimated resource/cost information when available

A successful backend call is only a staged result. HAL accepts it only after artifact verification, provenance recording and motion QC.

Planned adapters:
- comfyui_wan
- ltx
- reality_stage

No renderer owns family identity, voice authorization, episode state or release authority.
