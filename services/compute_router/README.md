# HAL Compute Router

Small production control-plane service for HAL's provider mesh.

It deliberately does **not** perform GPU inference. It reports provider health/capabilities and makes fail-closed routing decisions. GPU workers remain replaceable execution backends.

Endpoints:
- GET /v1/health
- GET /v1/capabilities
- POST /v1/route

Railway runs this service from the HAL_SUPREME monorepo with root directory `/services/compute_router`.
