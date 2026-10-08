# MCP C# SDK #1904 — source review

Issue: https://github.com/modelcontextprotocol/csharp-sdk/issues/1904

## Fresh issue state

- Open.
- No open pull request referencing #1904 was found at review time.
- Source review only; no local reproduction or test execution is claimed.

## Current source

Reviewed on current main:

`src/ModelContextProtocol.Core/Server/AIFunctionMcpServerTool.cs`

Blob SHA:

`82b6ceb9d18a0fb5fbedef6841c7a80f6972fcb5`

The current `CreateAIFunctionFactoryOptions` implementation builds a `ConfigureParameterBinding` delegate that closes over `McpServerToolCreateOptions options`.

Inside that delegate, the only service-provider-dependent construction-time check is whether a method parameter is recognized by `IServiceProviderIsService`.

The actual invocation-time binding already resolves the dependency from `args.Services`, not from the construction-time root provider.

## Compatibility-first repair shape

Avoid retaining the full create-options object or root service provider in the parameter-binding delegate.

A bounded approach is:

1. At tool creation, inspect the method parameters against `IServiceProviderIsService`.
2. Snapshot only the parameter types that should be DI-bound into a small immutable set.
3. Make `ConfigureParameterBinding` close over that set instead of `options` or the root provider.
4. Keep invocation-time resolution from `args.Services` unchanged.

This preserves the existing schema contract while removing the root provider from the cached descriptor's closure graph.

## Regression matrix

- normal DI parameter remains excluded from JSON schema and resolves at invocation;
- `[FromKeyedServices]` behavior remains unchanged;
- ordinary non-service parameters remain in schema;
- repeated host create/map/dispose allows prior root service providers to become unreachable under `WeakReference` checks.

## Claim boundary

No local reproduction, test execution, patch, ownership claim, or upstream PR is claimed.
