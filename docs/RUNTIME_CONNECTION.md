# Runtime Connection Strategy

HAL accepts video workers through two immediate paths:

1. **Local ComfyUI** — direct ComfyUI API adapter at the machine-local endpoint.
2. **Remote HAL Video Worker** — provider-agnostic HTTPS contract that can front a rented GPU, cloud VM, home GPU, or future provider adapter.

The control plane never gives the worker release authority. A worker returns a candidate artifact; HAL still applies artifact, temporal-motion and provenance gates.

## Security
Do not expose an unauthenticated ComfyUI port to the public internet. Remote workers should use TLS plus an authorization token and firewall restrictions.

## Fastest production route
Use whichever healthy worker appears first. The capability router makes the backend replaceable, so a temporary rented/cloud worker can generate today's video while local ComfyUI is installed or repaired.
