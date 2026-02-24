#!/usr/bin/env python3
"""
Proton VPN Integration Demo

Demonstrates secure VPN connectivity for penetration testing:
- Anonymous reconnaissance
- IP rotation
- Secure C2 communications
- Multi-hop connections (Secure Core)

Author: SHAdd0WTAka
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.protonvpn import ProtonVPNManager, VPNProtocol, VPNSecurityLevel


async def demo_basic_connection():
    """Demonstrate basic VPN connection"""
    print("\n" + "=" * 60)
    print("  Proton VPN - Basic Connection Demo")
    print("=" * 60 + "\n")

    vpn = ProtonVPNManager()

    # Get original IP
    print("[1] Getting original IP address...")
    original_ip = await vpn.get_public_ip()
    print(f"    Original IP: {original_ip}")

    # Connect to Switzerland (privacy-friendly)
    print("\n[2] Connecting to Switzerland...")
    print("    This provides strong privacy protection...")
    status = await vpn.connect(country="CH", protocol=VPNProtocol.WIREGUARD)

    if status.connected:
        print("    ✅ Connected!")
        print(f"    Location: {status.server_location}")
        print(f"    Protocol: {status.protocol}")
        print(f"    New IP: {status.public_ip}")
        print(f"    Kill Switch: {'Enabled' if status.kill_switch else 'Disabled'}")

        # Verify IP change
        if status.public_ip != original_ip:
            print("    ✅ IP successfully changed!")
        else:
            print("    ⚠️  IP might not have changed (check VPN)")
    else:
        print("    ❌ Connection failed")

    # Show connection history
    print("\n[3] Connection History:")
    history = vpn.get_connection_history()
    for conn in history:
        print(f"    - {conn['timestamp']}: {conn['server']} ({conn['public_ip']})")

    # Disconnect
    print("\n[4] Disconnecting...")
    await vpn.disconnect()
    print("    ✅ Disconnected")


async def demo_secure_core():
    """Demonstrate Secure Core (multi-hop) connection"""
    print("\n" + "=" * 60)
    print("  Proton VPN - Secure Core (Multi-Hop) Demo")
    print("=" * 60 + "\n")

    vpn = ProtonVPNManager()

    print("[Secure Core Explanation]")
    print(
        """
    Secure Core routes your traffic through two servers:
    1. Entry Server (in a privacy-friendly country)
       ↓ Encrypted tunnel
    2. Exit Server (your selected country)
       ↓ Internet

    This protects against:
    - Compromised exit servers
    - Traffic correlation attacks
    - Advanced adversaries
    """
    )

    print("[1] Connecting via Secure Core...")
    status = await vpn.connect(
        country="CH", security_level=VPNSecurityLevel.SECURE_CORE, protocol=VPNProtocol.WIREGUARD, kill_switch=True
    )

    if status.connected:
        print("    ✅ Secure Core connected!")
        print(f"    Path: Privacy-friendly country → {status.server_location}")
        print(f"    Public IP: {status.public_ip}")
        print("    Protection: Maximum anonymity")

    await vpn.disconnect()


async def demo_ip_rotation():
    """Demonstrate IP rotation for anonymity"""
    print("\n" + "=" * 60)
    print("  Proton VPN - IP Rotation Demo")
    print("=" * 60 + "\n")

    vpn = ProtonVPNManager()

    print("[Use Case: Pentest with IP rotation]")
    print("    Rotating IPs helps avoid:")
    print("    - Rate limiting by target")
    print("    - IP-based blocking")
    print("    - Detection by blue teams")
    print()

    countries = ["CH", "NL", "SE"]

    for i, country in enumerate(countries, 1):
        print(f"[{i}] Connecting to {country}...")
        status = await vpn.connect(country=country)

        if status.connected:
            print(f"    IP: {status.public_ip}")
            print(f"    Location: {status.server_location}")

            # Simulate pentest activity
            print("    Performing reconnaissance...")
            await asyncio.sleep(1)

            if i < len(countries):
                print("    Rotating to next IP...")
                await vpn.disconnect()
                await asyncio.sleep(1)

    await vpn.disconnect()
    print("\n    ✅ Rotation complete")


async def demo_server_selection():
    """Demonstrate intelligent server selection"""
    print("\n" + "=" * 60)
    print("  Proton VPN - Smart Server Selection")
    print("=" * 60 + "\n")

    vpn = ProtonVPNManager()

    print("[1] Available Servers:")
    servers = await vpn.get_server_list()
    for server in servers:
        features = ", ".join(server.features) if server.features else "Standard"
        print(f"    {server.name}: {server.city}, {server.country}")
        print(f"      Load: {server.load}% | Features: {features}")

    print("\n[2] Recommended Servers by Purpose:")

    purposes = ["pentest", "c2", "fileshare", "general"]
    for purpose in purposes:
        server = await vpn.recommend_server(
            purpose=purpose, require_p2p=(purpose == "fileshare"), require_secure_core=(purpose == "pentest")
        )
        if server:
            print(f"    {purpose:12} → {server.name} ({server.city}, Load: {server.load}%)")

    print("\n[3] P2P-Optimized Servers:")
    p2p_servers = await vpn.get_server_list()
    p2p_servers = [s for s in p2p_servers if "p2p" in s.features]
    for server in p2p_servers[:3]:
        print(f"    - {server.name}: {server.city} (Load: {server.load}%)")


async def demo_pentest_workflow():
    """Demonstrate VPN integration in pentest workflow"""
    print("\n" + "=" * 60)
    print("  Proton VPN - Pentest Workflow Integration")
    print("=" * 60 + "\n")

    print(
        """
    [Scenario: External Penetration Test]

    As a penetration tester, you need to:
    1. Hide your real IP address
    2. Avoid attribution
    3. Bypass geo-restrictions
    4. Maintain secure C2 communications
    """
    )

    vpn = ProtonVPNManager()

    # Phase 1: Initial Setup
    print("[Phase 1] Initial Setup with VPN")
    print("    Connecting to secure server...")
    status = await vpn.connect(country="CH", security_level=VPNSecurityLevel.SECURE_CORE, kill_switch=True)

    if status.connected:
        print("    ✅ VPN tunnel established")
        print(f"    Public IP: {status.public_ip}")
        print("    Kill Switch: ACTIVE")

        # Phase 2: Reconnaissance
        print("\n[Phase 2] Anonymous Reconnaissance")
        print("    Tools used:")
        print("      - theHarvester (email gathering)")
        print("      - Shodan (service discovery)")
        print("      - Nmap (port scanning)")
        print(f"    Source IP: {status.public_ip} (protected)")

        # Phase 3: IP Rotation
        print("\n[Phase 3] IP Rotation after scan detection")
        print("    Target might detect scanning...")
        print("    Rotating IP address...")

        new_status = await vpn.rotate_ip(country="NL")
        print(f"    New IP: {new_status.public_ip}")
        print("    Continuing scan from new location...")

        # Phase 4: C2 Setup
        print("\n[Phase 4] Secure C2 Communication")
        print("    Setting up encrypted channel...")
        print(f"    C2 Traffic routed through: {new_status.server_location}")
        print("    Protocol: WireGuard (fast & secure)")

        # Phase 5: Data Exfiltration (simulated)
        print("\n[Phase 5] Secure Data Transfer")
        print("    Findings encrypted and transferred")
        print("    DNS leak protection: Active")
        print("    IPv6 leak protection: Active")

    await vpn.disconnect()

    print("\n[Cleanup]")
    print("    VPN disconnected")
    print("    Connection logs cleared")
    print("    ✅ Pentest complete with full anonymity")


async def demo_leak_protection():
    """Demonstrate leak protection features"""
    print("\n" + "=" * 60)
    print("  Proton VPN - Leak Protection Check")
    print("=" * 60 + "\n")

    vpn = ProtonVPNManager()

    print("[Connecting with maximum protection...]")
    await vpn.connect(country="CH", protocol=VPNProtocol.WIREGUARD, kill_switch=True)

    print("\n[Running leak tests...]")
    results = vpn.check_ip_leak()

    print(f"\nDNS Leak: {'DETECTED' if results['dns_leak'] else 'None'}")
    print(f"WebRTC Leak: {'DETECTED' if results['webrtc_leak'] else 'None'}")
    print(f"IPv6 Leak: {'DETECTED' if results['ipv6_leak'] else 'None'}")

    print("\n[DNS Servers]")
    for dns in results.get("dns_servers", []):
        print(f"  {dns}")

    print("\n[Recommendations]")
    for rec in results.get("recommendations", []):
        print(f"  ✅ {rec}")

    await vpn.disconnect()


async def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("  ZEN AI PENTEST - Proton VPN Integration")
    print("  Secure & Anonymous Penetration Testing")
    print("=" * 60)

    demos = [
        ("Basic Connection", demo_basic_connection),
        ("Secure Core (Multi-Hop)", demo_secure_core),
        ("IP Rotation", demo_ip_rotation),
        ("Server Selection", demo_server_selection),
        ("Pentest Workflow", demo_pentest_workflow),
        ("Leak Protection", demo_leak_protection),
    ]

    for i, (name, demo_func) in enumerate(demos, 1):
        try:
            await demo_func()
        except Exception as e:
            print(f"\n❌ Demo '{name}' failed: {e}")

        if i < len(demos):
            input("\n⏎ Press Enter to continue...")

    print("\n" + "=" * 60)
    print("  All demos completed!")
    print("=" * 60)
    print(
        """
Proton VPN Integration Features:
✅ Anonymous reconnaissance
✅ IP rotation & switching
✅ Secure Core (multi-hop)
✅ Kill switch protection
✅ P2P-optimized servers
✅ Leak protection (DNS, WebRTC, IPv6)
✅ Smart server selection
✅ Pentest workflow integration

For production use:
1. Install Proton VPN: https://protonvpn.com/
2. Install CLI: protonvpn-cli
3. Login: protonvpn-cli login
4. Use this module for automated operations
    """
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        sys.exit(0)
