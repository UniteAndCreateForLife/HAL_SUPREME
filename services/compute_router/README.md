# HAL Compute Router

Small production control-plane service for HAL's provider mesh.

It deliberately does **not** perform GPU inference. It reports provider health/capabilities and makes fail-closed routing decisions. GPU workers remain replaceable execution backends.

Endpoints:
- GET /v1/health
- GET /v1/capabilities
- POST /v1/route

Provider flags are opt-in and default to disabled:
- `HAL_PROVIDER_HUGGINGFACE_ENABLED`
- `HAL_PROVIDER_CLOUDFLARE_ENABLED`
- `HAL_PROVIDER_MODAL_ENABLED`
- `HAL_PROVIDER_LOCAL_ENABLED`

Cloudflare Workers AI is represented as bounded edge inference (LLM, embeddings, speech, image and vision). Modal is represented as serverless GPU capacity for inference, training/fine-tuning, scientific workloads, media jobs and sandboxes. The router exposes no provider credentials and selects a provider only when that provider explicitly advertises the requested capability.

Railway runs this service from the HAL_SUPREME monorepo with root directory `/services/compute_router`.
