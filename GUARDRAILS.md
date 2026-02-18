# Security Guardrails 🛡️

Input validation and safety controls for Zen-AI-Pentest to prevent accidental damage to critical infrastructure.

---

## Overview

The guardrails module provides multiple layers of protection:

1. **IP Validation** - Blocks private/internal networks
2. **Domain Validation** - Blocks localhost/internal domains
3. **Risk Levels** - Controls which tools can run
4. **Rate Limiting** - Prevents abuse and accidental DoS

---

## IP Validation

Blocks scanning of private and sensitive IP ranges.

### Blocked Networks

| Range | Description |
|-------|-------------|
| 10.0.0.0/8 | Private Class A |
| 172.16.0.0/12 | Private Class B |
| 192.168.0.0/16 | Private Class C |
| 127.0.0.0/8 | Loopback |
| 169.254.0.0/16 | Link-local |
| 224.0.0.0/4 | Multicast |
| ::1/128 | IPv6 Loopback |
| fe80::/10 | IPv6 Link-local |

### Usage

```python
from guardrails import validate_target

# Blocks private IP
result = validate_target("192.168.1.1")
print(result.is_valid)  # False
print(result.reason)    # "IP 192.168.1.1 is in blocked network range(s): 192.168.0.0/16"

# Allows public IP
result = validate_target("8.8.8.8")
print(result.is_valid)  # True
```

### Exceptions

```python
from guardrails.ip_validator import get_ip_validator

validator = get_ip_validator()
validator.add_exception("scanme.nmap.org")
```

---

## Domain Validation

Blocks scanning of internal/sensitive domains.

### Blocked Patterns

- `localhost` and variations (`*.localhost`, `localhost.*`)
- `.local` TLD
- `.internal` TLD
- `.corp` TLD
- `.home` TLD
- IP addresses in URLs
- `file://` URLs

### Usage

```python
from guardrails import validate_domain, validate_url

# Blocks localhost
result = validate_domain("localhost")
print(result.is_valid)  # False

# Blocks internal domain
result = validate_domain("server.local")
print(result.is_valid)  # False

# Blocks file URLs
result = validate_url("file:///etc/passwd")
print(result.is_valid)  # False
```

---

## Risk Levels

Controls which security tools can be executed based on risk level.

### Levels

| Level | Value | Description | Tools Allowed |
|-------|-------|-------------|---------------|
| SAFE | 0 | Reconnaissance only | whois, dns, subdomain |
| NORMAL | 1 | Standard scanning | + nmap, web_enum, nuclei |
| ELEVATED | 2 | Light exploitation | + sqlmap, exploit |
| AGGRESSIVE | 3 | Full exploitation | + pivot, lateral |

### Usage

```python
from guardrails import RiskLevel, can_run_tool, validate_tool
from guardrails.risk_levels import set_risk_level

# Set risk level
set_risk_level(RiskLevel.NORMAL)

# Check if tool allowed
print(can_run_tool("nmap"))     # True
print(can_run_tool("sqlmap"))   # False

# Validate with flags
result = validate_tool("nmap", ["-T5"])
print(result["allowed"])        # False (dangerous flag)
print(result["blocked_flags"])  # ["-T5"]
```

### Tool Profiles

```python
from guardrails.risk_levels import RiskLevelManager, ToolRiskProfile

manager = RiskLevelManager(RiskLevel.NORMAL)

# Add custom tool
profile = ToolRiskProfile(
    name="custom_scanner",
    min_risk_level=RiskLevel.NORMAL,
    description="Custom vulnerability scanner",
    dangerous_flags=["--destructive"],
)
manager.add_tool_profile(profile)
```

---

## Rate Limiting

Prevents excessive tool execution to avoid:
- Accidental DoS against targets
- Excessive resource usage
- Detection by defensive systems

### Limits

- **Global**: 100 requests/hour per user
- **Per-target**: 20 requests/hour per target
- **Per-tool**: 30 requests/hour per tool
- **Burst**: Max 3-10 requests per second
- **Cooldown**: 1-5 seconds between requests

### Usage

```python
from guardrails import check_tool_execution

async def run_scan():
    # Check rate limit
    result = await check_tool_execution("nmap", "scanme.nmap.org", user_id="user123")
    
    if not result["allowed"]:
        print(f"Rate limited: {result['reason']}")
        print(f"Wait {result['wait_seconds']} seconds")
        return
    
    # Execute tool...
```

---

## Integration

### Full Validation Chain

```python
from guardrails import (
    validate_target,
    validate_domain,
    can_run_tool,
    check_tool_execution,
)
from guardrails.risk_levels import RiskLevel, set_risk_level

async def safe_execute(tool_name: str, target: str, user_id: str):
    # 1. Validate IP
    ip_result = validate_target(target)
    if not ip_result.is_valid:
        return {"error": ip_result.reason}
    
    # 2. Validate Domain
    domain_result = validate_domain(target)
    if not domain_result.is_valid:
        return {"error": domain_result.reason}
    
    # 3. Check Risk Level
    if not can_run_tool(tool_name):
        return {"error": f"Tool {tool_name} not allowed at current risk level"}
    
    # 4. Check Rate Limit
    rate_result = await check_tool_execution(tool_name, target, user_id)
    if not rate_result["allowed"]:
        return {"error": rate_result["reason"]}
    
    # Safe to execute
    return {"allowed": True}
```

---

## Tests

All guardrails have comprehensive tests:

```bash
# Run guardrails tests
pytest tests/test_guardrails.py -v

# Results: 55 tests passing ✅
```

### Test Coverage

- **IP Validator**: 15 tests
- **Domain Validator**: 13 tests
- **Risk Levels**: 14 tests
- **Rate Limiter**: 12 tests
- **Integration**: 1 test

---

## Configuration

### Environment Variables

```bash
# Set default risk level
DEFAULT_RISK_LEVEL=1  # 0=SAFE, 1=NORMAL, 2=ELEVATED, 3=AGGRESSIVE

# Disable guardrails (DANGEROUS!)
DISABLE_GARDRAILS=false
```

### Custom Blocked Networks

```python
from guardrails.ip_validator import IPValidator

validator = IPValidator([
    "10.0.0.0/8",
    "192.168.0.0/16",
    "custom.range/24",
])
```

---

## Safety First! ⚠️

**Never disable guardrails in production!**

These controls exist to prevent:
- Scanning your own infrastructure
- Violating scope agreements
- Legal liability
- Production outages

Always validate targets before scanning!
