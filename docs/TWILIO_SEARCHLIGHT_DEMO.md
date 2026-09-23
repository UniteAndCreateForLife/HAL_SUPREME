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
