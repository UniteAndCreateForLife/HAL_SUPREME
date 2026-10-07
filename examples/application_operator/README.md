# HAL Application Operator

This module is the control plane for a human-gated job-application agent. It is
intended to let HAL or an AI assistant prepare application forms quickly while
preserving truthful representations and a verifiable submission trail.

## Operating model

1. **Discover** a paid opportunity from an authorized source.
2. **Qualify** it against skills, compensation, geography, fees, and platform rules.
3. **Prepare** a field-by-field plan from an approved profile and role-specific drafts.
4. **Review** any legal, work-authorization, compensation, demographic, background,
   signature, consent, identity, or other attestation fields with the user.
5. **Approve** the exact prepared plan using its digest-bound approval phrase.
6. **Submit** only through a supported browser/API/MCP path and only after approval.
7. **Receipt** the provider's confirmation before changing state to `submitted`.
8. Continue through assessment, interview, acceptance, match, delivery, and payment
   without collapsing those states into one another.

## Site adapters

Prefer official APIs and MCP servers. For Contra, use Contra's official MCP where a
needed capability is exposed; its write actions use prepare -> confirm. Do not use
scrapers, bots, anti-bot bypasses, or scripted access that conflicts with a site's
terms. When a job application is not available through an official integration,
use a normal user-authorized browser session and stop at any CAPTCHA, MFA, identity,
legal attestation, tax, bank, payment, or other human-only step.

## Approved profile

Keep personal application data outside the public repository. A local profile can
contain only fields the user has explicitly approved for reuse, for example:

```json
{
  "name": "Example Person",
  "email": "person@example.com",
  "location": "Chicago, IL",
  "website": "https://example.com",
  "portfolio": "https://example.com/work",
  "github": "https://github.com/example"
}
```

Never store passwords, MFA/OTP codes, SSNs, tax IDs, bank/card data, or protected
identity documents in the application profile.

## Tests

```bash
python -m unittest -v examples.application_operator.test_application_operator
```

The tests cover routine autofill, legal/demographic confirmation gates, CAPTCHA and
OTP blocking, draft-only narrative answers, digest-bound approval, and receipt-bound
submission state.
