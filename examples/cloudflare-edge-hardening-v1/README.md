# HAL Cloudflare Edge Hardening Reference v1

Public-safe deployment reference for the existing `hal-chat` Worker.

## Security changes

- Adds a dedicated `chat` mode.
- Unknown modes fail back to `chat`.
- Caps `max_tokens` per mode.
- Adds a stricter limiter for `build`, `expert`, and `council`.
- Drops client-supplied `tools`, `tool_choice`, provider overrides, and system messages.
- Limits body size, message count, and aggregate message characters.
- Allows only configured browser origins.
- Uses Turnstile server-side validation to issue short-lived signed browser session tokens.
- Requires bearer authorization for chat when enabled; trusted mobile/CLI clients use a separate explicit API bearer.
- Adds Workers AI degraded fallback without pretending local HAL memory/tools are available.
- Returns explicit degraded provenance.
- Uses bindings/secrets instead of embedding credentials.

## Production integration notes

The current live `hal-chat` source was not available in the public HAL repository when this reference was prepared. Do **not** deploy this file blindly over production. Port the helper logic into the current Worker or compare routes first.

Required secrets:
- `HAL_GATEWAY_URL`
- `HAL_GATEWAY_TOKEN`
- `HAL_TURNSTILE_SECRET` for browser session issuance
- `HAL_SESSION_SECRET` for HMAC-signed 15-minute browser sessions
- `HAL_API_BEARER` only if trusted non-browser clients are needed

Recommended variables:
- `HAL_ALLOWED_ORIGINS`
- `HAL_REQUIRE_AUTH=1`
- `HAL_EDGE_FALLBACK_ENABLED=0` until zero-spend readiness is verified
- `HAL_EDGE_FALLBACK_MODEL`

Required bindings:
- `AI`
- `CHAT_RATE_LIMITER`
- `HEAVY_RATE_LIMITER`

## Safe deployment sequence

1. Export/back up the current Worker source/config.
2. Compare live routes with this reference; preserve speech/transcription/image routes.
3. Add the two rate-limit bindings with unique namespace IDs.
4. Add Turnstile, a session-signing secret, and (only if needed) a trusted API bearer in Cloudflare Secrets.
5. Keep Workers AI fallback disabled initially.
6. Deploy to a preview/staging Worker.
7. Verify origin rejection, Turnstile missing/replay/expired behavior, session issuance/expiry, missing/invalid bearer rejection, token caps, `tools` stripping, chat/fast/build/expert/council routing, heavy-mode limits, and gateway-down behavior.
8. Verify zero secret leakage in logs/responses.
9. Enable fallback only after confirming zero-spend entitlement/rate limits.
10. Promote to `hal-chat` and retain rollback version.

## Important boundary

Workers AI fallback is **degraded chat**, not HAL continuity. It must never claim access to local memory, files, tools, agents, computer state, or private persona/audio state. The home gateway remains authoritative for full HAL behavior.
