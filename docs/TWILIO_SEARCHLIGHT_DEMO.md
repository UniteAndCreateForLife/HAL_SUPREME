# HAL Twilio Searchlight demo

This is a bounded Twilio Messaging integration for the Twilio AI Startup Searchlight application path. It is engineering evidence only: it is not an application receipt, honoree selection, credit award, or payment receipt.

## Architecture

`Twilio Messaging -> HTTPS webhook -> Twilio SDK signature validation -> HAL decision endpoint -> TwiML reply -> Twilio`

The webhook validates `X-Twilio-Signature` using Twilio's official Python SDK before HAL is invoked. Invalid or incomplete requests fail closed. The HAL request forwards only the channel, Twilio MessageSid, and bounded message body; phone numbers are not forwarded by this bridge.

Safe event logs contain a hashed message reference, decision identifier, elapsed time, and status. They do not log the Twilio auth token, phone number, or message body.

## Configuration boundary

Required environment variable names:

- `TWILIO_AUTH_TOKEN`
- `HAL_TWILIO_WEBHOOK_URL` — the exact public URL configured in Twilio
- `HAL_SEARCHLIGHT_DECISION_URL` — the existing HAL decision service endpoint

No Twilio credential was detected in the automation environment and no external Twilio API request was made during this milestone. Dependencies were installed only in this worktree's ignored `.venv`; no global/system package was installed.

The health endpoint explicitly reports `live_twilio_account_verified=false`. That stays false until an authorized operator verifies the account and performs a real end-to-end Twilio interaction.

## Live-demo gate

Before representing this as a working Twilio product demo, an authorized human/operator must:

1. verify the Twilio account and applicable account/program state;
2. expose this webhook at a public HTTPS URL and configure that exact URL in Twilio;
3. send a real inbound message through Twilio and capture the signed inbound/outbound receipt;
4. verify the HAL decision path and TwiML response end to end;
5. review the resulting one- or two-scenario demo before using it in the Searchlight application.

Startup funding, applicant age, representation authority, account ownership, and final application declarations are human-only attestations. This code does not infer or submit them.

## Source-bound local rehearsal

Before a live Twilio account is connected, run the local rehearsal to prove the bridge accepts a correctly signed Twilio webhook, forwards only the minimized HAL payload, returns TwiML, and rejects an invalid signature without invoking HAL:

```bash
python -m services.twilio_searchlight_demo.rehearsal --output <receipt.json>
```

The generated receipt is bound to the current Git commit and explicitly records `live_twilio_account_verified=false` and `external_twilio_api_call=false`. It is development evidence only and must not be described as the required live Twilio-integrated Searchlight demo.

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
