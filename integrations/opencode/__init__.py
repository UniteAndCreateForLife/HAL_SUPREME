"""Bounded OpenCode integration for HAL SUPREME."""

from .worker import (
    OpenCodeClient,
    OpenCodeError,
    OpenCodeProtocolError,
    OpenCodeSecurityError,
)

__all__ = [
    "OpenCodeClient",
    "OpenCodeError",
    "OpenCodeProtocolError",
    "OpenCodeSecurityError",
]
