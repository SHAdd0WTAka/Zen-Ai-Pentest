"""API Routes Module"""

from . import agents, auth, findings, reports, scans, system, vpn, websocket

__all__ = [
    "auth",
    "scans",
    "findings",
    "reports",
    "agents",
    "vpn",
    "system",
    "websocket",
]
