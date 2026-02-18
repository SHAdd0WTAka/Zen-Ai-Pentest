"""
VPN Integration for Zen-AI-Pentest
===================================

Optional VPN support for secure penetration testing.
Currently supports ProtonVPN.

Features:
- VPN connection status checking
- Automatic kill switch recommendations
- Warnings when scanning without VPN
- Graceful degradation (works without VPN)

Usage:
    from vpn import VPNManager, get_vpn_manager
    
    vpn = get_vpn_manager()
    if vpn.is_connected():
        print("VPN active - safe to scan")
    else:
        print("WARNING: Scanning without VPN protection")
"""

from .protonvpn import ProtonVPNManager, VPNStatus, VPNManager
from .decorators import require_vpn, recommend_vpn

__all__ = [
    "ProtonVPNManager",
    "VPNStatus", 
    "VPNManager",
    "require_vpn",
    "recommend_vpn",
    "get_vpn_manager",
]

# Global instance
_vpn_manager = None


def get_vpn_manager() -> VPNManager:
    """Get or create global VPN manager instance"""
    global _vpn_manager
    if _vpn_manager is None:
        _vpn_manager = VPNManager()
    return _vpn_manager
