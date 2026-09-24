from __future__ import annotations

import re

DEFAULT_TENANT_ID = "demo-campus"
# 1-64 lowercase alphanumeric/hyphen characters, with alphanumeric boundaries.
# The optional suffix permits two-character tenant IDs while still rejecting
# leading/trailing hyphens and overlong scopes.
TENANT_ID_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")

ROLE_ACTIONS = {
    "analyst": frozenset({"case:read", "report:analyze", "review:write"}),
    "reviewer": frozenset({"case:read", "report:analyze", "audit:read", "review:write", "review:close"}),
    "auditor": frozenset({"case:read", "audit:read", "review:write"}),
}


def validate_tenant_id(tenant_id: str) -> str:
    """Validate a non-secret tenant scope used only for authorization boundaries."""
    if not isinstance(tenant_id, str) or not TENANT_ID_RE.fullmatch(tenant_id):
        raise ValueError("invalid tenant_id")
    return tenant_id


def authorize_action(
    *,
    actor_role: str,
    action: str,
    actor_tenant_id: str,
    resource_tenant_id: str,
) -> None:
    """Fail closed unless role permission and tenant scope both match."""
    actor_tenant_id = validate_tenant_id(actor_tenant_id)
    resource_tenant_id = validate_tenant_id(resource_tenant_id)
    if actor_tenant_id != resource_tenant_id:
        raise PermissionError("cross-tenant access denied")
    allowed = ROLE_ACTIONS.get(actor_role)
    if allowed is None:
        raise PermissionError("unknown actor role")
    if action not in allowed:
        raise PermissionError(f"role {actor_role} is not authorized for {action}")
