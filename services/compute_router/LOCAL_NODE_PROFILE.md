# HAL Local Compute Node Profile v1

This is a deliberately small control-plane contract for describing **owned local compute** without auto-disclosing host identity, filesystem paths, account identifiers, or credentials.

It does not provision hardware, start inference, or claim that HAL is already a distributed compute network.

## Why this exists

HAL's public compute router already fails closed around remote provider cost/entitlement. This module adds a complementary local-first primitive: an operator can publish a bounded description of an owned node's capacity and declared capabilities while keeping sensitive machine details out of the public control plane.

The profile is intended to support reproducible local-compute experiments, CI fixtures, and future cluster/bootstrap work.

## Profile contract

Schema: `hal.local-node-profile.v1`

Stable fields:

- `enabled`
- `owner_controlled`
- `remote_dependency`
- `budget_policy`
- `capabilities`
- `capacity.cpu_cores`
- `capacity.ram_gib`
- `capacity.gpu_model`
- `capacity.gpu_vram_gib`
- disclosure flags proving which sensitive classes are intentionally absent

Capacity is **operator-declared**. The module does not probe the hostname, user account, filesystem, cloud credentials, or local secret stores.

## Configuration

All values are optional and default to a safe disabled/unknown state.

```text
HAL_PROVIDER_LOCAL_ENABLED=true
HAL_LOCAL_NODE_CAPABILITIES=inference,coding
HAL_LOCAL_NODE_CPU_CORES=16
HAL_LOCAL_NODE_RAM_GIB=119
HAL_LOCAL_NODE_GPU_MODEL=example-gpu
HAL_LOCAL_NODE_GPU_VRAM_GIB=8
```

If numeric capacity fields are missing, malformed, or negative, they resolve to `null` rather than being guessed.

## Run the contract tests

```bash
python -m unittest tests.test_local_node_profile -v
```

The dedicated GitHub Actions workflow also compiles/lints the module and uploads:

```text
evidence/local-node-profile-ci/profile.json
evidence/local-node-profile-ci/SHA256SUMS
```

The CI sample uses synthetic/example capacity values. It is evidence for the profile contract, not proof of the maintainer's physical workstation capacity.

## Next bounded step

After this profile contract is green in CI, the next integration step is to let the existing compute router reference the profile for `local_hal` routing while preserving the current fail-closed provider behavior and existing tests.

A later node bootstrap should separately prove:

1. local runtime installation,
2. local model discovery,
3. health/capacity measurement,
4. lease/concurrency behavior,
5. interruption/recovery,
6. cost/energy observations,
7. multi-node federation without weakening owner control.

Those are future acceptance gates, not current claims.
