---
name: poc-validator
description: Proof-of-Concept (PoC) Validation Skill for security exploit verification. Use when validating exploitability of vulnerabilities, generating tailored payloads, executing exploits in sandboxed environments, or verifying successful exploitation (e.g., SQL injection, CVE exploitation, command injection). Triggers on tasks involving payload generation, exploit execution verification, sandboxed testing, or confirmation of administrative access/data exfiltration after exploitation attempts.
---

# PoC-Validator Skill

Validates vulnerability exploitability through controlled payload generation, sandboxed execution, and success verification.

## Quick Start

Generate and validate a PoC for SQL injection:
```python
from scripts.payload_generator import PayloadGenerator
from scripts.sandbox_executor import SandboxExecutor
from scripts.verify_exploit import ExploitVerifier

# Generate payload
gen = PayloadGenerator()
payload = gen.generate_sql_payload(
    target_url="http://target.com/login",
    parameter="username",
    technique="error_based"
)

# Execute in sandbox
executor = SandboxExecutor()
result = await executor.execute_sqlmap(
    target="http://target.com/login",
    payload=payload,
    risk_level=2
)

# Verify success
verifier = ExploitVerifier()
is_exploitable = await verifier.verify_sql_injection(result)
```

## Workflow

### 1. Payload Generation

Use `scripts/payload_generator.py` for:
- **CVE-based exploits**: Lookup known payloads from vulnerability_mapping.json
- **SQL Injection**: Error-based, Union-based, Time-based, Boolean-based
- **Command Injection**: System command payloads with evasion techniques
- **Path Traversal**: Directory traversal sequences
- **XXE/XML Injection**: External entity payloads

See [references/payload_patterns.md](references/payload_patterns.md) for complete payload library.

### 2. Sandbox Execution

Use `scripts/sandbox_executor.py` for isolated exploit testing:
- Docker container isolation with resource limits
- Network isolation (no egress to private ranges)
- Execution timeouts (default: 300s)
- Read-only filesystem with tmpfs for output
- Automatic cleanup post-execution

**Critical**: All exploit execution MUST use sandbox. Never run exploits directly on host.

### 3. Success Verification

Use `scripts/verify_exploit.py` to confirm exploitation:
- **SQL Injection**: Detect database version extraction, table enumeration
- **RCE**: Verify command output in response
- **Auth Bypass**: Confirm session token/admin access
- **Data Exfiltration**: Detect sensitive data patterns in responses
- **File Upload**: Verify file presence/execution

## Risk Levels

| Level | Payload Type | Tools | Use Case |
|-------|-------------|-------|----------|
| 0 | Passive detection | None | Vulnerability confirmation only |
| 1 | Safe payloads | SQLMap --risk 1 | Non-destructive testing |
| 2 | Active exploitation | SQLMap --risk 2, Metasploit | Controlled exploitation |
| 3 | Aggressive | All tools with full payloads | Full PoC validation |

## Integration with Zen-AI-Pentest

```python
# Integration with ExploitAgent
from autonomous.exploit_validator import ExploitValidator

def validate_poc(self, vulnerability: dict) -> dict:
    """Validate vulnerability with PoC execution."""
    validator = ExploitValidator(
        sandbox_enabled=True,
        risk_level=vulnerability.get("risk", 1)
    )

    return validator.validate(
        vuln_type=vulnerability["type"],
        target=vulnerability["target"],
        evidence=vulnerability["evidence"]
    )
```

## Safety Controls

Before any exploit execution:
1. Validate target is not in private ranges (guardrails/ip_validator.py)
2. Confirm explicit authorization in database
3. Set execution timeout
4. Enable Docker sandbox
5. Log all actions to audit trail

See [references/safety_requirements.md](references/safety_requirements.md) for complete safety checklist.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Sandbox timeout | Payload too slow | Increase timeout or use faster technique |
| Container crash | Resource exhaustion | Reduce threads, increase memory limit |
| Network blocked | Egress filtering | Verify allowed outbound in config |
| Verification failed | WAF/IPS blocking | Try evasion techniques from payload_patterns.md |

## Output Format

```json
{
  "poc_id": "uuid",
  "vulnerability_id": "vuln-123",
  "status": "verified|failed|inconclusive",
  "exploit_type": "sql_injection|rce|xxe|...",
  "payload_used": "...",
  "sandbox_logs": "...",
  "evidence": {
    "before": "...",
    "after": "...",
    "extracted_data": "..."
  },
  "risk_level": 2,
  "timestamp": "2026-03-20T14:46:00Z",
  "verified_by": "exploit_agent_v3"
}
```

## References

- [Payload Patterns Library](references/payload_patterns.md) - Complete payload collection
- [Sandbox Setup Guide](references/docker_sandbox_setup.md) - Docker configuration details
- [Safety Requirements](references/safety_requirements.md) - Mandatory safety checks
- [CVE Database Schema](references/cve_schema.md) - CVE lookup structure

## Scripts

- `scripts/payload_generator.py` - Generate tailored exploit payloads
- `scripts/sandbox_executor.py` - Execute exploits in Docker sandbox
- `scripts/verify_exploit.py` - Verify exploitation success
- `scripts/cleanup_sandbox.py` - Clean up sandbox resources
