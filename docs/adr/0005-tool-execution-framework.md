# ADR 0005: Tool Execution Framework

## Status
Proposed

## Context
Need to integrate real security tools (nmap, nuclei, sqlmap, etc.) not just generate suggestions.

## Decision
Build a unified tool execution framework with containerized runners.

## Architecture

### Tool Interface
```python
class Tool(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...
    
    @abstractmethod
    async def execute(self, target: str, options: dict) -> ToolResult: ...
    
    @property
    def safety_level(self) -> SafetyLevel:
        return SafetyLevel.READ_ONLY
```

### Execution Modes

#### 1. Local (Development)
Direct subprocess execution.
```python
proc = await asyncio.create_subprocess_exec(
    "nmap", "-sV", target,
    stdout=asyncio.subprocess.PIPE
)
```

#### 2. Containerized (Production)
Docker with network restrictions.
```yaml
# docker-compose.tools.yml
services:
  nmap:
    image: instrumentisto/nmap
    network_mode: host
    read_only: true
    security_opt:
      - no-new-privileges:true
```

#### 3. Remote (Scale)
Kubernetes jobs for distributed scanning.
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: nmap-scan-{uuid}
spec:
  template:
    spec:
      containers:
      - name: nmap
        image: instrumentisto/nmap
        args: ["-sV", "target"]
      restartPolicy: Never
```

### Safety Levels
```python
class SafetyLevel(Enum):
    READ_ONLY = 1      # Passive recon only
    NON_DESTRUCTIVE = 2  # Active but safe
    DESTRUCTIVE = 3    # May modify state
    EXPLOIT = 4        # Full exploitation
```

## Tool Categories

| Category | Tools | Safety |
|----------|-------|--------|
| Recon | nmap, masscan, amass | READ_ONLY |
| Web | nuclei, ffuf, gospider | NON_DESTRUCTIVE |
| Vuln Scan | sqlmap (dry-run), nikto | NON_DESTRUCTIVE |
| Exploit | metasploit, sqlmap (exec) | EXPLOIT |
| AD | bloodhound, responder | NON_DESTRUCTIVE |
| Cloud | pacu, scoutsuite | NON_DESTRUCTIVE |

## Output Parsing
Standardized result format:
```json
{
  "tool": "nmap",
  "version": "7.94",
  "target": "10.0.0.1",
  "duration": 45.2,
  "findings": [
    {
      "type": "open_port",
      "port": 80,
      "service": "http",
      "version": "Apache 2.4.41"
    }
  ],
  "raw_output": "..."
}
```

## Consequences

### Positive
- Real tool execution
- Accurate results
- Industry-standard tools

### Negative
- Docker dependency
- Tool installation complexity
- Version management

## References
- [OWASP Offensive Tools](https://owasp.org/www-community/Free_for_Open_Source_Application_Security_Tools)
