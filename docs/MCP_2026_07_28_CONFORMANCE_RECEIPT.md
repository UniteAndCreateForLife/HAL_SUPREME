# MCP 2026-07-28 Conformance Receipt

This note defines the reproducible protocol check for HAL MCP work.

Official suite: https://github.com/modelcontextprotocol/conformance

## Run

```bash
npx @modelcontextprotocol/conformance list --requirements 2026-07-28
npx @modelcontextprotocol/conformance server --url http://localhost:3000/mcp --requirements 2026-07-28
```

Use the frozen `2026-07-28` requirement set. The official suite runs this revision with the stateless wire model and per-request `_meta`. A result from an older stateful lifecycle is not evidence for this revision.

An expected-failures baseline can keep CI useful while gaps are known, but a baselined failure is still a conformance failure.

## Record

For every public result record:

- exact HAL source commit;
- target fixture or owned endpoint;
- conformance-runner version;
- requirements set;
- UTC timestamp;
- required pass/fail counts;
- not-scored scenarios;
- whether an expected-failures baseline was used;
- SHA-256 of the retained raw report.

## Keep separate

Official MCP conformance tests protocol behavior. HAL-specific controls such as authority boundaries, approval gates, retry/idempotency behavior, provider-cost policy, provenance, and execution-state validation remain separate acceptance dimensions.

HAL distinguishes configured, authorized, attempted, observed, validated, and reported states. Do not claim success when the contract requires a later state that was not observed.

## Next proof

Run the official requirement set against one public-safe HAL MCP fixture, attach the raw report hash to this PR, and report protocol conformance independently from HAL-specific acceptance results.
