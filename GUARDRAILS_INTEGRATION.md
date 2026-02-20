# Guardrails Integration ✅

This document describes how security guardrails are integrated into the workflow orchestrator and task processor.

---

## Overview

Guardrails are now **automatically enforced** in:

1. **Workflow Orchestrator** - Validates targets before workflow starts
2. **Task Creation** - Filters tools based on risk level
3. **Task Processor** - Rate limits tool execution

---

## Integration Points

### 1. Target Validation (Orchestrator)

When `start_workflow()` is called, the target is validated:

```python
orchestrator = WorkflowOrchestrator()

# ❌ BLOCKED - Private IP
await orchestrator.start_workflow(
    workflow_type="network_recon",
    target="192.168.1.1",  # Raises ValueError
    agents=["agent-1"]
)

# ✅ ALLOWED - Public IP
await orchestrator.start_workflow(
    workflow_type="network_recon",
    target="8.8.8.8",  # Success
    agents=["agent-1"]
)
```

**Blocked Targets:**
- Private IPs (10.x, 172.16-31.x, 192.168.x)
- Loopback (127.x, ::1)
- Link-local (169.254.x, fe80::)
- Localhost and .local domains
- File:// URLs

### 2. Risk Level Enforcement

Tools are filtered based on risk level:

```python
from guardrails.risk_levels import RiskLevel

# SAFE level - only reconnaissance
orchestrator = WorkflowOrchestrator(risk_level=RiskLevel.SAFE)
# Allows: whois, dns, subdomain
# Blocks: nmap, nuclei, sqlmap, exploit

# NORMAL level - standard scanning
orchestrator = WorkflowOrchestrator(risk_level=RiskLevel.NORMAL)
# Allows: + nmap, nuclei, web_enum
# Blocks: sqlmap, exploit

# ELEVATED level - light exploitation
orchestrator = WorkflowOrchestrator(risk_level=RiskLevel.ELEVATED)
# Allows: + sqlmap, exploit
# Blocks: pivot, lateral

# AGGRESSIVE level - everything
orchestrator = WorkflowOrchestrator(risk_level=RiskLevel.AGGRESSIVE)
# Allows: all tools including pivot, lateral
```

### 3. Rate Limiting (Task Processor)

Tools are rate limited at execution time:

```python
async def process_task(self, task: Dict, user_id: Optional[str] = None):
    # Check rate limit
    rate_limit_result = await check_tool_execution(tool, target, user_id)

    if not rate_limit_result["allowed"]:
        return TaskResult(
            status="blocked",
            error=f"Rate limited: {rate_limit_result['reason']}"
        )

    # Execute tool...
```

**Limits:**
- 100 requests/hour per user (global)
- 20 requests/hour per target
- 30 requests/hour per tool

---

## Configuration

### Default Risk Level

```python
# Normal scanning (default)
orchestrator = WorkflowOrchestrator()  # risk_level=RiskLevel.NORMAL

# Explicit level
orchestrator = WorkflowOrchestrator(risk_level=RiskLevel.SAFE)
```

### Disable Guardrails (DANGEROUS!)

```python
# Only disable if you know what you're doing!
orchestrator = WorkflowOrchestrator()
orchestrator.guardrails_enabled = False
```

---

## Error Messages

### Target Validation Failed

```
ValueError: Target validation failed: IP validation failed:
IP 192.168.1.1 is in blocked network range(s): 192.168.0.0/16
```

### Rate Limited

```
TaskResult:
  status: "blocked"
  error: "Rate limited: Rate limit exceeded. Blocked for 60.0s"
```

### Tool Blocked by Risk Level

```
⚠️  Guardrails blocked tool 'sqlmap': Tool 'sqlmap' not allowed at
risk level NORMAL. Blocked tools: sqlmap, exploit, pivot, lateral
```

---

## Test Results

All 21 integration tests passing ✅

```bash
pytest tests/test_guardrails_integration.py -v

# Results:
# - Target validation: 7 tests ✅
# - Risk levels: 4 tests ✅
# - File URLs: 1 test ✅
# - IPv6: 2 tests ✅
# - Class B: 2 tests ✅
# - Configuration: 5 tests ✅
```

---

## Example Usage

```python
import asyncio
from agents.workflows.orchestrator import WorkflowOrchestrator
from guardrails.risk_levels import RiskLevel

async def main():
    # Create orchestrator with SAFE risk level
    orch = WorkflowOrchestrator(
        step_timeout=300,
        risk_level=RiskLevel.SAFE
    )

    # This will succeed
    workflow_id = await orch.start_workflow(
        workflow_type="network_recon",
        target="scanme.nmap.org",
        agents=["agent-1"]
    )
    print(f"Workflow started: {workflow_id}")

    # This will fail
    try:
        await orch.start_workflow(
            workflow_type="network_recon",
            target="192.168.1.1",
            agents=["agent-1"]
        )
    except ValueError as e:
        print(f"Blocked: {e}")

asyncio.run(main())
```

---

## Security First! 🛡️

**Never disable guardrails in production!**

These controls protect against:
- Accidental internal network scanning
- Legal liability from out-of-scope testing
- Production system damage
- Reputation damage

Always validate your targets!
