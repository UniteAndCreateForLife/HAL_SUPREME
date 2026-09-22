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
- lightx2v_wan22 — direct LightX2V Wan2.2 TI2V worker. The first strict 8GB/Turing canary profile uses torch SDPA plus phase/CPU/T5/VAE offload at 480p before verified mastering.
- ltx — adapter boundary only; current LTX community-license models remain blocked by the strict-open-source policy.

Quantization is not silently enabled. LightX2V requires a matching quantized checkpoint when quantized DiT/T5 modes are selected, so HAL's baseline config stays on the original Wan2.2 weights. An INT8 path may be added only after a converted/verified checkpoint is present and recorded in provenance.

## Windows low-VRAM bootstrap

The runtime stays isolated from HAL's main Python environment:

    powershell -ExecutionPolicy Bypass -File scripts\bootstrap_nightmare_video_runtime.ps1
    powershell -ExecutionPolicy Bypass -File scripts\bootstrap_nightmare_video_runtime.ps1 -Install -DownloadModel
    python scripts\nightmare_runtime_doctor.py
    python scripts\run_lightx2v_canary.py

The bootstrap does not expose a server publicly. Model weights remain outside Git.

No renderer owns family identity, voice authorization, episode state or release authority.
