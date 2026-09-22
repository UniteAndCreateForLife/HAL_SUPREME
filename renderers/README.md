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

Implemented adapters:
- comfyui_wan — local ComfyUI queue adapter.
- lightx2v_wan22 — direct LightX2V Wan2.2 TI2V worker. The strict 8GB/Turing profile uses torch SDPA, INT8, phase/CPU/VAE offload and 480p canary output before verified mastering.
- ltx — adapter boundary only; current LTX community-license models remain blocked by the strict-open-source policy.

Planned/auxiliary adapters:
- reality_stage

## Windows low-VRAM bootstrap

The runtime stays isolated from HAL's main Python environment:

    powershell -ExecutionPolicy Bypass -File scripts\bootstrap_nightmare_video_runtime.ps1
    powershell -ExecutionPolicy Bypass -File scripts\bootstrap_nightmare_video_runtime.ps1 -Install -DownloadModel
    python scripts\nightmare_runtime_doctor.py
    python scripts\run_lightx2v_canary.py

The bootstrap does not expose a server publicly. Model weights remain outside Git.

No renderer owns family identity, voice authorization, episode state or release authority.
