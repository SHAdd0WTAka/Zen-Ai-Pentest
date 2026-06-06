# ProtonVPN Integration 🔒

Optional VPN support for secure penetration testing. Recommended but not required.

---

## Overview

The VPN integration provides **optional** security enhancements for penetration testing:

- ✅ **Works without VPN** - System functions normally without VPN
- ⚠️ **Warns without VPN** - Shows recommendations when scanning without protection
- 🔒 **Optional strict mode** - Can require VPN for scans (configurable)
- 🌐 **ProtonVPN support** - Native integration with ProtonVPN CLI
- 🔍 **Generic detection** - Works with any VPN (OpenVPN, WireGuard, etc.)

---

## Installation

### Install ProtonVPN CLI (Optional)

```bash
# Install ProtonVPN CLI
pip install protonvpn-cli

# Or on Ubuntu/Debian
sudo apt install protonvpn-cli

# Login
sudo protonvpn-cli login

# Connect to VPN
sudo protonvpn-cli connect
```

**Without ProtonVPN CLI**: System works normally, just shows warnings.

---

## Usage

### Basic Usage (No VPN Required)

```python
from agents.workflows.orchestrator import WorkflowOrchestrator

# Works without VPN - just shows warning
orchestrator = WorkflowOrchestrator()
workflow_id = await orchestrator.start_workflow(
    workflow_type="network_recon",
    target="scanme.nmap.org",
    agents=["agent-1"]
)
# Output: ⚠️ WARNING: Scanning without VPN protection!
#         💡 Recommendation: Connect to ProtonVPN before scanning
```

### Check VPN Status

```python
from vpn import get_vpn_manager

vpn = get_vpn_manager()

if vpn.is_connected():
    status = vpn.get_status()
    print(f"✅ VPN active: {status.provider}")
    print(f"   Server: {status.server}")
    print(f"   IP: {status.ip}")
else:
    print("⚠️  No VPN connection")
```

### Manual VPN Check

```python
from vpn import check_vpn_before_scan

result = check_vpn_before_scan("target.com")

if result["warning"]:
    print(result["warning"])      # Warning message
if result["recommendation"]:
    print(result["recommendation"])  # How to connect

# Scan proceeds regardless (unless strict mode)
print(f"Allowed: {result['allowed']}")
```

---

## Configuration

### Strict Mode (Require VPN)

```python
from vpn import get_vpn_manager

vpn = get_vpn_manager()
vpn.set_strict_mode(True)

# Now scans require VPN
result = vpn.check_before_scan("target.com")
# Without VPN: result["allowed"] = False
```

### Disable Warnings

```python
from vpn import get_vpn_manager

vpn = get_vpn_manager()
vpn.set_recommendations(False)

# No more warnings
```

---

## Decorators

### @recommend_vpn (Non-blocking)

```python
from vpn.decorators import recommend_vpn

@recommend_vpn()
async def scan_target(target: str):
    # Shows warning if no VPN, but executes anyway
    return await run_nmap(target)
```

### @require_vpn (Blocking)

```python
from vpn.decorators import require_vpn

@require_vpn()
async def scan_target(target: str):
    # Raises PermissionError if no VPN
    return await run_nmap(target)
```

---

## VPN Status

### Status Values

```python
from vpn.protonvpn import VPNStatus

status = vpn.get_status()

if status.status == VPNStatus.CONNECTED:
    print("🔒 VPN connected")
elif status.status == VPNStatus.DISCONNECTED:
    print("🔓 VPN disconnected")
elif status.status == VPNStatus.UNKNOWN:
    print("❓ VPN status unknown")
elif status.status == VPNStatus.ERROR:
    print(f"❌ VPN error: {status.error_message}")
```

### VPN Information

```python
status = vpn.get_status()

print(f"Provider: {status.provider}")    # "ProtonVPN"
print(f"Server: {status.server}")        # "CH#1"
print(f"IP: {status.ip}")                # "10.0.0.1"
print(f"Country: {status.country}")      # "Switzerland"
print(f"Protocol: {status.protocol}")    # "UDP"
```

---

## CLI Commands

### Check VPN Status

```bash
# Via ProtonVPN CLI
protonvpn-cli status

# Output:
# Status:       Connected
# Server:       CH#1
# Country:      Switzerland
# IP:           185.159.156.XX
# Protocol:     UDP
```

### Connect/Disconnect

```python
from vpn.protonvpn import ProtonVPNManager

proton = ProtonVPNManager()

# Connect
proton.connect()                    # Auto-select server
proton.connect("CH#1")              # Specific server

# Disconnect
proton.disconnect()
```

---

## Supported VPNs

### Native Support
- **ProtonVPN** (via CLI)

### Generic Detection
Any VPN that creates these interfaces:
- `tun0`, `tun1` (OpenVPN)
- `wg0`, `wg1` (WireGuard)
- `ppp0` (PPTP/L2TP)
- `proton0` (ProtonVPN)

Or runs these processes:
- `openvpn`
- `wireguard` / `wg`
- `protonvpn`
- `nordvpn`
- `expressvpn`
- `mullvad`

---

## Security Recommendations

### Why Use VPN?

1. **Hide your real IP** - Target can't identify you
2. **Bypass geo-restrictions** - Test from different countries
3. **Protect your identity** - Especially for aggressive testing
4. **Avoid ISP throttling** - Some ISPs block scanning
5. **Legal protection** - In some jurisdictions

### When VPN is Critical

- 🚨 Aggressive exploitation (Risk Level 3)
- 🚨 Production environment testing
- 🚨 Testing outside your country
- 🚨 Testing sensitive targets

### When VPN is Optional

- ✅ Local test environments
- ✅ Authorized penetration tests
- ✅ Your own infrastructure
- ✅ Public bug bounty programs

---

## Testing

```bash
# Run VPN tests
pytest tests/test_vpn.py -v

# Results: 35+ tests passing ✅
```

---

## Troubleshooting

### "ProtonVPN CLI not installed"

**Solution**: VPN integration works without CLI, just install for full features:
```bash
pip install protonvpn-cli
```

### VPN connected but not detected

**Check**:
```bash
# Linux
ip link show | grep tun

# macOS
ifconfig | grep utun

# Check processes
ps aux | grep -i vpn
```

### Strict mode blocking legitimate scans

**Solution**: Disable strict mode or add exceptions:
```python
vpn.set_strict_mode(False)

# Or check specific networks
@require_vpn(allowed_networks=["127.0.0.1", "192.168.1.0/24"])
```

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Workflow      │────▶│   VPN Check      │────▶│   Guardrails    │
│  Orchestrator   │     │   (Optional)     │     │   Validation    │
│                 │     │                  │     │                 │
│                 │◄────│   Warning Only   │◄────│   Block/Allow   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │  ProtonVPN CLI   │
                        │  Generic Detect  │
                        └──────────────────┘
```

---

**Remember**: VPN is recommended but optional. The system works perfectly without it! 🔒✨
