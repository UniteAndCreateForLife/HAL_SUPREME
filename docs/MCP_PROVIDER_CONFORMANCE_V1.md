# MCP Provider Conformance Checklist v1

HAL SUPREME treats MCP servers as replaceable workers. This checklist is a
provider-neutral admission/evaluation artifact for deciding whether an MCP-backed
provider is sufficiently observable and bounded to participate in HAL workflows.

It separates MCP protocol behavior from HAL policy controls. A provider can
implement MCP correctly and still fail HAL's local authorization, cost,
provenance, or authority requirements.

## Current protocol reference

The current stable MCP SDK line implements protocol revision `2026-07-28`.
That revision uses the modern stateless lifecycle; older protocol revisions use
the initialization handshake. HAL must not assume one lifecycle without first
observing or negotiating the actual server/client behavior.

Canonical references:

- https://modelcontextprotocol.io/
- https://ts.sdk.modelcontextprotocol.io/v2/
- https://go.sdk.modelcontextprotocol.io/protocol/

This checklist is not an MCP certification.

## Evidence states

Every control is recorded as one of:

- `verified` — directly observed by a reproducible public test or receipt.
- `documented` — described in public documentation but not independently re-run by this fixture.
- `not_observed` — not demonstrated by the available evidence.
- `not_applicable` — the control does not apply to this provider shape.

A `verified` or `documented` result must cite public evidence. A missing
observation is not converted into a pass.

## Protocol-facing controls

### P1 — Transport is explicit
Record the transport actually used: stdio, Streamable HTTP, or another
documented MCP transport.

### P2 — Protocol/lifecycle behavior is explicit
Record the observed protocol revision when available. If the revision was not
captured, say `not_recorded`.

### P3 — Capabilities/tools are discovered at runtime
Enumerate the current public surface rather than freezing a stale tool list into
HAL.

### P4 — Tool schemas are inspectable before mutation
For tools that can change external state, the current input schema should be
available before execution.

### P5 — Authentication boundary is distinguishable
Record whether the observed connection is anonymous/keyless, authenticated, or
unknown. Public evidence records the boundary, never credential values.

## HAL admission controls

### H1 — Read vs mutation authority is explicit
A broad MCP connection is not treated as blanket authorization.

### H2 — Protected actions retain an approval gate
Spending, purchases, public writes, submissions, contracts, identity/tax/bank
actions, and equivalent protected mutations remain gated unless a narrower
reviewed policy explicitly authorizes them.

### H3 — Timeout/failure behavior is bounded
Connections and calls require finite timeouts. Retries, when used, must be
bounded and must not conceal authoritative errors or duplicate mutations.

### H4 — Provenance can survive provider replacement
HAL should retain enough public-safe metadata to explain which provider/tool was
used, what class of action occurred, and what verification was performed.

### H5 — Provider does not become canonical task/release authority
An MCP server may execute work, but it must not silently become the owner of
HAL's durable task state, approval state, revenue truth, or release decision.

### H6 — Private operational material stays outside public evidence
Conformance evidence records names/classes of auth boundaries, never credential
values, private client data, private connector material, or account identifiers.

## Machine-readable record

Records live under `examples/mcp_conformance/` and contain:

- provider identifier and observation date;
- transport and protocol revision, including `not_recorded` where necessary;
- all eleven control IDs (`P1`–`P5`, `H1`–`H6`);
- evidence state;
- concise finding;
- public evidence references for `verified` and `documented` states.

Validate records with:

```bash
python scripts/validate_mcp_conformance.py
python -m unittest -v tests.test_mcp_provider_conformance
```

## First public mapping

The first fixture maps the existing Livepeer Creative MCP integration. It does
not claim a negotiated MCP protocol revision because the public evidence did not
record one. It does record evidence for Streamable HTTP usage, runtime catalog
and schema discovery, explicit spend gates, provider-as-worker authority, and
provenance policy.

This distinction is intentional:

> A server connection and tool catalog prove connectivity. They do not prove
> that execution is authorized, affordable, safe, or release-ready.
