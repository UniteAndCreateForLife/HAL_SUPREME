from __future__ import annotations

from .protocol import Action, Observation


def greedy_resource_policy(observation: Observation) -> Action:
    """Deterministic baseline: gather here, otherwise approach best visible resource."""

    resources = sorted(
        observation.visible_resources,
        key=lambda item: (-int(item["value"]), str(item["resource_id"])),
    )
    x, y = observation.position

    for resource in resources:
        rx, ry = int(resource["position"][0]), int(resource["position"][1])
        if (rx, ry) == (x, y):
            return Action("gather")

    if not resources:
        return Action("idle")

    target = resources[0]["position"]
    tx, ty = int(target[0]), int(target[1])

    if tx > x:
        return Action("move", dx=1)
    if tx < x:
        return Action("move", dx=-1)
    if ty > y:
        return Action("move", dy=1)
    if ty < y:
        return Action("move", dy=-1)
    return Action("idle")
