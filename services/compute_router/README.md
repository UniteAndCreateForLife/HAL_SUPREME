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

Cloudflare Workers AI and Modal have an additional fail-closed zero-spend gate:
- `HAL_PROVIDER_CLOUDFLARE_ZERO_SPEND_READY`
- `HAL_PROVIDER_MODAL_ZERO_SPEND_READY`

Both readiness flags also default to `false`. Enabling a remote provider therefore does not make it routable by itself. An operator or quota monitor must separately confirm that the current account is still inside an authorized free/sponsored allocation and set the matching readiness flag. The router does not infer billing-plan or remaining-credit state and must not set these flags automatically. Clear the flag when that state is unknown or stale.

Cloudflare Workers AI is represented as bounded edge inference (LLM, embeddings, speech, image and vision). Modal is represented as serverless GPU capacity for inference, training/fine-tuning, scientific workloads, media jobs and sandboxes. The router exposes no provider credentials and selects a provider only when that provider explicitly advertises the requested capability and satisfies any required zero-spend gate.

Railway runs this service from the HAL_SUPREME monorepo with root directory `/services/compute_router`.
## Verified-capacity admission

Remote capacity is fail-closed. A provider must be both explicitly enabled and, when applicable, explicitly marked zero-spend/credit-ready before `/v1/route` can select it. Provider metadata never includes credential values.

Supported control-plane providers include:
- `openrouter_free` â€” free-model text inference only
- `cloudflare_workers_ai` â€” Workers AI free allocation
- `nvidia_nim` â€” verified developer inference access
- `modal` â€” bounded free-credit GPU workloads
- `livepeer_creative` â€” registered-hacker media balance only
- `lightning_ai` â€” verified free-credit GPU workloads
- `huggingface` â€” only after an explicit ZeroGPU/free-only admission gate
- `github_actions` â€” public standard-runner build/test/benchmark/package compute
- `local_hal` â€” operator-managed private worker

Routing is priority-ordered within a capability and returns the selected provider's `budget_policy`, so downstream execution can preserve the same cost guard. The router still does not hold provider secrets or execute provider-specific jobs itself.
