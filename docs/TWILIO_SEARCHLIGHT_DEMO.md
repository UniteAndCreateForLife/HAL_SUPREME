# HAL Twilio Searchlight demo

This is a bounded Twilio Messaging integration for the Twilio AI Startup Searchlight application path. It is engineering evidence only: it is not an application receipt, honoree selection, credit award, or payment receipt.

## Architecture

`Twilio Messaging -> HTTPS webhook -> Twilio SDK signature validation -> HAL decision endpoint -> TwiML reply -> Twilio`

The webhook validates `X-Twilio-Signature` using Twilio's official Python SDK before HAL is invoked. Invalid or incomplete requests fail closed. The HAL request forwards only the channel, Twilio MessageSid, and bounded message body; phone numbers are not forwarded by this bridge.

Safe event logs contain a hashed message reference, decision identifier, elapsed time, and status. They do not log the Twilio auth token, phone number, or message body.

The HTTP envelope also fails closed before HAL is invoked: only `application/x-www-form-urlencoded` requests are accepted, request bodies are capped at 16 KiB, malformed/empty lengths are rejected, unsupported content types return HTTP 415, and oversized bodies return HTTP 413.

Twilio may retry a webhook when a response is delayed or interrupted. The bridge keeps a bounded ten-minute, process-local cache keyed only by SHA-256 digests of `MessageSid` and body. An identical retry reuses the verified TwiML response without invoking HAL twice; concurrent duplicates wait for the first result. Reuse of a `MessageSid` with different content fails closed with HTTP 409. Failed HAL calls are not cached, and the cache does not retain the raw MessageSid, request body, phone number, or auth token. This limits duplicate inference and provider cost within one process; multi-replica or restart-safe idempotency still requires a reviewed shared store.

## Configuration boundary

Required environment variable names:

- `TWILIO_AUTH_TOKEN`
- `HAL_TWILIO_WEBHOOK_URL` — the exact public URL configured in Twilio
- `HAL_SEARCHLIGHT_DECISION_URL` — for canonical HAL, `http://127.0.0.1:8766/operator/commands`
- `HAL_SEARCHLIGHT_RECEIPT_DIR` — optional writable directory for privacy-minimized successful-interaction receipts
- `HAL_SEARCHLIGHT_SOURCE_SHA` — exact 40-character deployed Git SHA; required when receipt capture is enabled

No Twilio credential was detected in the automation environment and no external Twilio API request was made during this milestone. Dependencies were installed only in this worktree's ignored `.venv`; no global/system package was installed.

The health endpoint explicitly reports `live_twilio_account_verified=false`. That stays false until an authorized operator verifies the account and performs a real end-to-end Twilio interaction.

## Canonical HAL decision path

For the live HAL path, set `HAL_SEARCHLIGHT_DECISION_URL` to the loopback Operator Gateway commands endpoint above. The bridge submits only an `operator.conversation` input: the bounded SMS body, a conversation ID derived from the MessageSid hash, `private_local` provider mode, and `FAST_PRIVATE_CHOICE` profile. It does not forward phone numbers or the raw MessageSid. HAL's existing command bus remains the operation authority; the bridge polls that operation and returns an SMS reply only when the operation is `VERIFIED` with a real provider response and model identifier. Failed, degraded, pending beyond the eight-second budget, and permission-waiting operations produce HTTP 503 from the webhook rather than an invented HAL answer.

The bridge binds to `127.0.0.1:8091` for a dedicated HTTPS tunnel. The Gateway and Runtime API must be healthy before the demo; this code does not start either service. HAL's canonical conversation store persists the SMS body as conversation content. The bridge's own event logs and interaction receipts omit it.

For local launch, install `services/twilio_searchlight_demo/requirements.txt` in this checkout's ignored virtual environment. Enter the Twilio Auth Token into an interactive, masked terminal prompt and set it only in the child process environment; do not put the token in command arguments, a `.env` file, this repository, chat, or receipt artifacts. For example, from a PowerShell session in this checkout after setting the exact public webhook URL:

```powershell
$env:HAL_TWILIO_WEBHOOK_URL = 'https://YOUR-TUNNEL-HOST/twilio/incoming'
$env:HAL_SEARCHLIGHT_DECISION_URL = 'http://127.0.0.1:8766/operator/commands'
$secureToken = Read-Host -AsSecureString 'Twilio Auth Token'
$env:TWILIO_AUTH_TOKEN = [System.Net.NetworkCredential]::new('', $secureToken).Password
try {
  & .\.venv\Scripts\python.exe -m services.twilio_searchlight_demo.app
} finally {
  Remove-Item Env:\TWILIO_AUTH_TOKEN -ErrorAction SilentlyContinue
  $secureToken.Dispose()
}
```

Enable interaction receipt capture only after this source is committed and the deployed SHA is verified; otherwise a stale `HAL_SEARCHLIGHT_SOURCE_SHA` would misrepresent the code that handled a real message. A successful local signed-webhook test does not establish a working Twilio trial response; verify the trial account's inbound-message behavior in the Console before claiming an end-to-end reply.

## Interaction receipt capture

When `HAL_SEARCHLIGHT_RECEIPT_DIR` and an exact deployed `HAL_SEARCHLIGHT_SOURCE_SHA` are configured, each successful signature-validated webhook can write an atomic JSON receipt named only by the existing hashed message reference. The receipt records source SHA, decision id, elapsed time, and hashes of the configured HTTPS webhook URL and returned TwiML. It does **not** record phone numbers, message bodies, auth tokens, or the raw webhook URL.

Receipt creation is fail-closed on an invalid source SHA, a non-success event, or a non-HTTPS configured webhook. A receipt is technical transport evidence only; it does not prove Twilio account ownership, program eligibility, application submission, honoree selection, credits, award, or payment. Those states remain false/human-gated until independently evidenced.

## Live-demo gate

Before representing this as a working Twilio product demo, an authorized human/operator must:

1. verify the Twilio account and applicable account/program state;
2. expose this webhook at a public HTTPS URL and configure that exact URL in Twilio;
3. send a real inbound message through Twilio and capture the signed inbound/outbound receipt;
4. verify the HAL decision path and TwiML response end to end;
5. review the resulting one- or two-scenario demo before using it in the Searchlight application.

Startup funding, applicant age, representation authority, account ownership, and final application declarations are human-only attestations. This code does not infer or submit them.

## Source-bound local rehearsal

Before a live Twilio account is connected, run the local rehearsal to exercise the bridge with a Twilio SDK signature and a mock Operator Gateway. It verifies the canonical `operator.conversation` payload shape, TwiML serialization, and that an invalid signature is rejected before the mock Gateway is called:

```bash
python -m services.twilio_searchlight_demo.rehearsal --output <receipt.json>
```

The generated receipt is bound to the current Git commit and explicitly records `live_twilio_account_verified=false` and `external_twilio_api_call=false`. It stores only the mock command field names and a hash of the synthetic message body. It is development evidence only: it does not prove a real Twilio request, a live HAL Gateway operation, or provider inference. The rehearsal also verifies invalid signatures, unsupported content types, and oversized request bodies are rejected before any mock Gateway call.

## Judge-readiness packet

The official Searchlight guidance asks for one clear end-to-end story, an obvious AI decision moment, an unmistakable Twilio role, a lightweight architecture explanation, impact, and a credible path to production. The current official page also requires a Twilio account and a working functional Twilio-integrated demo before application submission.

Generate a source-bound packet from a passing rehearsal receipt:

```bash
python -m services.twilio_searchlight_demo.judge_packet \
  --rehearsal <rehearsal-receipt.json> \
  --json-output <judge-packet.json> \
  --markdown-output <judge-packet.md>
```

The packet fails closed on a stale source SHA, a failing rehearsal, non-minimized HAL payload evidence, or any rehearsal receipt that tries to promote itself into live-account, submission, award, credit, payment, or spend evidence. It maps the technical evidence to the published judging criteria while leaving market claims, startup/account eligibility, live Twilio verification, and final submission as explicit human/account gates.

## Container deployment handoff

A minimal non-root container is provided under `services/twilio_searchlight_demo/Dockerfile` for local packaging checks. The bridge binds to `127.0.0.1`, and the Operator Gateway adapter also accepts only loopback URLs. The current image therefore cannot serve traffic through Docker port publishing or reach a host Gateway from an isolated container. Treat container deployment as blocked until a reviewed networking design preserves those local-only trust boundaries.

Build from the service directory:

```bash
docker build -t hal-twilio-searchlight:local services/twilio_searchlight_demo
```

The image declares port `8091`, exposes `/v1/health` inside the container, runs as uid `10001`, and includes an in-container healthcheck. These facts do not establish host reachability or a deployment route. Runtime credentials and endpoint values are supplied only as environment variables; they are not baked into the image.

A live deployment still requires the authorized operator to provide `TWILIO_AUTH_TOKEN`, `HAL_TWILIO_WEBHOOK_URL`, and `HAL_SEARCHLIGHT_DECISION_URL`. Receipt capture additionally requires a writable mounted directory plus exact `HAL_SEARCHLIGHT_SOURCE_SHA`. Building or locally running this image is not evidence of a live Twilio account, public deployment, Searchlight submission, award, or payment.
