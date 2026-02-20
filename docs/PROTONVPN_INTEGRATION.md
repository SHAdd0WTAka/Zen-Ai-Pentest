# Proton VPN Integration for Zen AI Pentest

## Overview

Secure VPN integration for anonymous penetration testing operations. Proton VPN provides military-grade encryption, strict no-logs policy, and secure core architecture - perfect for ethical hackers who need privacy and security.

## Why Proton VPN for Pentesting?

| Feature | Benefit for Pentesters |
|---------|----------------------|
| **No-Logs Policy** | Verified by audits, no connection records |
| **Secure Core** | Multi-hop VPN (resists traffic analysis) |
| **Kill Switch** | Prevents IP leaks if VPN drops |
| **WireGuard** | Fast, modern protocol with low overhead |
| **P2P Support** | Optimized for file sharing/exfiltration |
| **Tor over VPN** | Additional anonymity layer |

## Installation

### 1. Install Proton VPN CLI

```bash
# Linux (Debian/Ubuntu)
wget -q -O - https://repo.protonvpn.com/debian/public_key | apt-key add -
add-apt-repository 'deb https://repo.protonvpn.com/debian unstable main'
apt-get update && apt-get install protonvpn-cli

# macOS
brew install protonvpn-cli

# Windows
# Download from: https://protonvpn.com/download/
```

### 2. Login

```bash
protonvpn-cli login
# Enter your Proton VPN credentials
```

### 3. Test Connection

```bash
protonvpn-cli connect
protonvpn-cli status
protonvpn-cli disconnect
```

## Usage in Zen AI Pentest

### Basic Connection

```python
from modules.protonvpn import ProtonVPNManager

vpn = ProtonVPNManager()

# Quick connect to best server
status = await vpn.connect()

# Connect to specific country
status = await vpn.connect(country="CH")  # Switzerland

# Check status
print(f"Connected: {status.connected}")
print(f"IP: {status.public_ip}")
print(f"Location: {status.server_location}")
```

### Secure Core (Multi-Hop)

```python
from modules.protonvpn import VPNSecurityLevel

# Maximum privacy: Entry -> Secure Country -> Exit
status = await vpn.connect(
    country="CH",
    security_level=VPNSecurityLevel.SECURE_CORE,
    kill_switch=True
)

# Traffic path:
# You -> Iceland (Entry) -> Switzerland (Exit) -> Internet
```

### IP Rotation

```python
# Rotate IP every N minutes during scan
for country in ["CH", "NL", "SE"]:
    status = await vpn.connect(country=country)

    # Run pentest activities
    await run_nmap_scan(target)

    # Rotate before detection
    await vpn.disconnect()
```

### Integration with Pentest Workflow

```python
async def secure_pentest(target: str):
    vpn = ProtonVPNManager()

    # Phase 1: Connect with maximum security
    await vpn.connect(
        country="CH",
        security_level=VPNSecurityLevel.SECURE_CORE,
        protocol=VPNProtocol.WIREGUARD,
        kill_switch=True
    )

    # Phase 2: Verify no leaks
    leak_test = vpn.check_ip_leak()
    if leak_test['dns_leak'] or leak_test['webrtc_leak']:
        raise Exception("VPN leak detected!")

    # Phase 3: Run pentest tools
    await reconnaissance(target)
    await scanning(target)

    # Phase 4: Rotate if needed
    if await check_rate_limit():
        await vpn.rotate_ip()

    # Phase 5: Cleanup
    await vpn.disconnect()
```

## Configuration

### Config File

Create `config/protonvpn.json`:

```json
{
  "default_country": "CH",
  "default_protocol": "wireguard",
  "kill_switch": true,
  "dns_leak_protection": true,
  "ipv6_leak_protection": true,
  "preferred_countries": ["CH", "IS", "SE", "NL"],
  "p2p_countries": ["NL", "CH", "IS", "SE"]
}
```

### Environment Variables

```bash
export PROTONVPN_USERNAME="your_username"
export PROTONVPN_PASSWORD="your_password"
export PROTONVPN_TIER="2"  # 0=Free, 1=Basic, 2=Plus, 3=Visionary
```

## API Reference

### ProtonVPNManager

#### Methods

| Method | Description | Parameters |
|--------|-------------|------------|
| `connect()` | Establish VPN connection | `country`, `protocol`, `security_level`, `kill_switch` |
| `disconnect()` | Close VPN connection | None |
| `rotate_ip()` | Get new IP address | `country`, `protocol` |
| `get_status()` | Get current connection status | None |
| `check_ip_leak()` | Test for IP/DNS leaks | None |
| `speed_test()` | Test connection speed | None |
| `recommend_server()` | Get best server for purpose | `purpose`, `require_p2p`, `require_secure_core` |
| `get_server_list()` | List available servers | `country` |

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `connected` | bool | Connection state |
| `status` | VPNStatus | Detailed status object |
| `current_server` | VPNServer | Connected server info |
| `connection_history` | List[Dict] | Connection log |

### Enums

```python
class VPNProtocol:
    WIREGUARD = "wireguard"      # Fast, modern
    OPENVPN_TCP = "openvpn-tcp"  # Reliable
    OPENVPN_UDP = "openvpn-udp"  # Fast, traditional

class VPNSecurityLevel:
    STANDARD = "standard"        # Regular servers
    SECURE_CORE = "secure-core"  # Multi-hop
    TOR = "tor"                  # VPN over Tor
    P2P = "p2p"                  # File sharing
```

## Real-World Scenarios

### Scenario 1: Anonymous OSINT

```python
# Before: Your real IP is exposed
# After: Traffic routed through VPN

async def anonymous_osint(target_domain: str):
    vpn = ProtonVPNManager()

    # Connect to neutral country
    await vpn.connect(country="IS")  # Iceland

    # Run OSINT tools
    await theharvester(target_domain)
    await shodan_search(target_domain)

    # All requests come from Iceland IP

    await vpn.disconnect()
```

### Scenario 2: C2 Infrastructure

```python
# Protect C2 communications

async def secure_c2():
    vpn = ProtonVPNManager()

    # P2P-optimized for stable connection
    await vpn.connect(
        country="NL",
        protocol=VPNProtocol.WIREGUARD,
        p2p=True
    )

    # Start C2 server
    # All C2 traffic encrypted and anonymized

    while True:
        await handle_beacon()

        # Rotate every hour
        if time_to_rotate():
            await vpn.rotate_ip()
```

### Scenario 3: Red Team Exercise

```python
async def red_team_operation():
    vpn = ProtonVPNManager()

    # Phase 1: Initial access
    await vpn.connect(country="CH", security_level=VPNSecurityLevel.SECURE_CORE)
    await send_phishing_emails()

    # Phase 2: Post-exploitation
    await vpn.rotate_ip(country="SE")
    await establish_persistence()

    # Phase 3: Data exfiltration
    await vpn.connect(country="NL", p2p=True)
    await exfiltrate_data()

    await vpn.disconnect()
```

## Security Best Practices

### 1. Always Enable Kill Switch

```python
# Prevents IP leaks
await vpn.connect(kill_switch=True)
```

### 2. Verify No Leaks

```python
# Before pentest activities
leak_test = vpn.check_ip_leak()
assert not leak_test['dns_leak']
assert not leak_test['webrtc_leak']
```

### 3. Use Secure Core for Sensitive Ops

```python
# Multi-hop for maximum privacy
await vpn.connect(security_level=VPNSecurityLevel.SECURE_CORE)
```

### 4. Rotate IPs Regularly

```python
# Every 30-60 minutes during active scanning
if time_since_last_rotation() > 1800:
    await vpn.rotate_ip()
```

### 5. Choose Appropriate Countries

```python
# Privacy-friendly countries
PRIVACY_COUNTRIES = ["CH", "IS", "SE"]  # Switzerland, Iceland, Sweden

# P2P-friendly
P2P_COUNTRIES = ["NL", "CH", "IS", "SE", "DE"]

# Avoid: Countries with data retention laws
```

## Troubleshooting

### Connection Issues

```bash
# Check Proton VPN status
protonvpn-cli status

# Reconnect
protonvpn-cli disconnect
protonvpn-cli connect

# Check logs
protonvpn-cli logs
```

### IP Still Visible

```python
# 1. Check for WebRTC leaks
# 2. Disable IPv6
# 3. Use Kill Switch

status = await vpn.connect(
    kill_switch=True,
    protocol=VPNProtocol.WIREGUARD
)
```

### Slow Connection

```python
# Choose server with low load
servers = await vpn.get_server_list()
best = min(servers, key=lambda s: s.load)

# Or use WireGuard (faster)
await vpn.connect(protocol=VPNProtocol.WIREGUARD)
```

## Demo

Run the demo:

```bash
cd examples
python protonvpn_demo.py
```

Demos included:
- Basic connection
- Secure Core (multi-hop)
- IP rotation
- Server selection
- Pentest workflow integration
- Leak protection checks

## Legal Notice

⚠️ **Important:** Only use VPN for legitimate penetration testing with proper authorization. VPN does not make illegal activities legal.

## References

- Proton VPN: https://protonvpn.com/
- Privacy Policy: https://protonvpn.com/privacy-policy
- Swiss Privacy Laws: https://www.protonvpn.com/blog/swiss-privacy/

---

*Stay safe, stay anonymous, stay ethical.*
