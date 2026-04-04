#!/usr/bin/env python3
"""
Port Security Demo for Zen-AI-Pentest
=====================================

Demonstrates secure port allocation with VPN detection and MITM protection.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.port_manager_integration import (
    PentestPortAllocator,
    SecurePortManager,
    ServiceType,
    print_security_status,
)


def demo_security_status():
    """Show current security status."""
    print_security_status()


def demo_vpn_detection():
    """Demonstrate VPN detection."""
    print("\n" + "=" * 60)
    print("🔍 VPN Detection Demo")
    print("=" * 60)

    pm = SecurePortManager()

    if pm.is_available:
        vpn_active = pm.vpn_active
        print(f"\nVPN Active: {'YES ⚠️' if vpn_active else 'No ✅'}")

        if pm._vpn_detector:
            interfaces = pm._vpn_detector.get_vpn_interfaces()
            if interfaces:
                print(f"Detected Interfaces: {', '.join(interfaces)}")
    else:
        print("\n❌ LocalPortManager Secure not available")
        print("   Install from: https://github.com/SHAdd0WTAka/LocalportManager")


def demo_service_registration():
    """Demonstrate secure service registration."""
    print("\n" + "=" * 60)
    print("🔧 Service Registration Demo")
    print("=" * 60)

    pm = SecurePortManager()

    if not pm.is_available:
        print("\n❌ LocalPortManager Secure not available")
        return

    # Example 1: Native service (always safe)
    print("\n1. Native Python Service (always safe):")
    url = pm.register_tool(
        "api-server",
        "python -m http.server {port}",
        service_type=ServiceType.NATIVE,
    )
    print(f"   Registered: {url}")

    # Example 2: Docker service (blocked if VPN active)
    print("\n2. Docker Service (blocked if VPN active):")
    if pm.vpn_active:
        print("   ⚠️  VPN is active - Docker will be BLOCKED")
        print("   Use --no-kill-switch to bypass (DANGEROUS)")
    else:
        url = pm.register_tool("grafana", "docker run -p {port}:3000 grafana/grafana")
        print(f"   Registered: {url}")

    # Example 3: Forced Docker (bypass kill switch)
    print("\n3. Forced Docker (bypass kill switch):")
    print("   ⚠️  This is DANGEROUS - MITM risk!")
    # url = pm.register_tool("risky", "docker run nginx", force_docker=True)


def demo_port_allocator():
    """Demonstrate intelligent port allocator."""
    print("\n" + "=" * 60)
    print("🧠 Smart Port Allocator Demo")
    print("=" * 60)

    allocator = PentestPortAllocator()

    async def run():
        # This automatically chooses the safest option
        url = await allocator.allocate(
            name="nmap-api",
            docker_cmd="docker run -p {port}:8080 zen-ai/nmap-api",
            native_cmd="python -m zen_ai.nmap_api --port {port}",
        )
        print(f"\nAllocated: {url}")
        print("   (Automatically chose safest option based on VPN status)")

    asyncio.run(run())


def demo_best_practices():
    """Show security best practices."""
    print("\n" + "=" * 60)
    print("📚 Security Best Practices")
    print("=" * 60)

    print("""
1. 🔒 Always use 127.0.0.1 binding
   GOOD:  docker run -p 127.0.0.1:8080:80 nginx
   BAD:   docker run -p 8080:80 nginx

2. 🚫 Never use --network host with VPN
   GOOD:  docker run --network bridge nginx
   BAD:   docker run --network host nginx

3. 🛡️ Use isolated networks for sensitive services
   docker network create --internal isolated
   docker run --network isolated postgres

4. ✅ Prefer native services when VPN is active
   Python/Node apps instead of Docker containers

5. 📊 Monitor security status regularly
   python -m core.port_manager_integration

6. 🚨 Enable kill switch in production
   export LPM_KILL_SWITCH=true
    """)


def demo_architecture():
    """Show secure architecture."""
    print("\n" + "=" * 60)
    print("🏗️ Secure Architecture")
    print("=" * 60)

    print("""
    ┌─────────────────────────────────────────────────────────────┐
    │              ZEN-AI-PENTEST Secure Architecture             │
    │                                                             │
    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
    │  │   Scanner    │  │   Analyzer   │  │   Reporter   │      │
    │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
    │         │                 │                 │              │
    │         └─────────────────┼─────────────────┘              │
    │                           │                                │
    │              ┌────────────┴────────────┐                  │
    │              │   SecurePortManager     │                  │
    │              │   (VPN Detection)       │                  │
    │              └────────────┬────────────┘                  │
    │                           │                                │
    │         ┌─────────────────┼─────────────────┐              │
    │         │                 │                 │              │
    │         ▼                 ▼                 ▼              │
    │   ┌──────────┐     ┌──────────┐     ┌──────────┐          │
    │   │  Native  │     │  Docker  │     │  Docker  │          │
    │   │  Service │     │ (No VPN) │     │ (Isolated)│         │
    │   │  :9001   │     │  :9002   │     │  :9003   │          │
    │   └──────────┘     └──────────┘     └──────────┘          │
    │                                                             │
    │   🔒 VPN Active = Docker blocked (MITM protection)         │
    └─────────────────────────────────────────────────────────────┘
    """)


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" 🔒 ZEN-AI-PENTEST Port Security Demo")
    print("=" * 70)

    demos = [
        ("Security Status", demo_security_status),
        ("VPN Detection", demo_vpn_detection),
        ("Service Registration", demo_service_registration),
        ("Smart Allocator", demo_port_allocator),
        ("Best Practices", demo_best_practices),
        ("Architecture", demo_architecture),
    ]

    print("\nAvailable demos:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")

    print("\n" + "=" * 70)

    for name, func in demos:
        try:
            func()
        except Exception as e:
            print(f"\n⚠️  {name} error: {e}")

    print("\n" + "=" * 70)
    print(" Demo complete!")
    print("=" * 70)
