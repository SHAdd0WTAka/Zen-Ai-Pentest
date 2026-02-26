# Tools & Integration

Zen-AI-Pentest integrates **72+ professional security tools** across all categories.

## Overview

| Category | Count | Tools |
|----------|-------|-------|
| **Network & Scanning** | 8 | Nmap, Masscan, Scapy, Tshark, tcpdump, netdiscover, arp-scan, wireshark |
| **Web Security** | 12 | BurpSuite, SQLMap, Gobuster, OWASP ZAP, FFuF, Nikto, WAFW00F, WhatWeb, Nuclei, curl, wget, httpx |
| **Reconnaissance** | 9 | Amass, Nuclei, TheHarvester, Subfinder, HTTPX, Sherlock, Ignorant, Scout, whois |
| **Exploitation** | 2 | Metasploit, SearchSploit |
| **Brute Force** | 4 | Hydra, Hashcat, John, Ncrack |
| **Active Directory** | 8 | BloodHound, NetExec, Responder, ldapsearch, rpcclient, smbclient, enum4linux |
| **Wireless** | 6 | Aircrack-ng Suite |
| **OSINT** | 4 | Sherlock, Ignorant, TheHarvester, Scout |
| **Code Analysis** | 4 | Semgrep, TruffleHog, Gitleaks, Bandit |
| **Container** | 3 | Trivy, Docker, Kubectl |
| **System Utilities** | 8 | Netcat, Socat, OpenSSL, Proxychains, Tor |
| **Core Framework** | 5 | Tool Registry, Tool Caller, Kimi CLI, Kimi Helper, AI Personas |
| **Total** | **72+** | |

## Complete Tools List

See [Complete Tools List](Tools-Complete-List.md) for detailed information on all 72+ tools.

## Tool Execution

### Direct

```python
from tools.executor import ToolExecutor

executor = ToolExecutor()
result = await executor.run(
    tool="nmap",
    target="example.com",
    options=["-sV", "-p", "80,443"]
)
```

### Via Agent

```python
from agents.cli import AgentCLI

cli = AgentCLI()
await cli.run_command("recon", target="example.com")
```

### Via API

```bash
curl -X POST http://localhost:8000/api/v1/tools/execute \
  -H "Authorization: Bearer <token>" \
  -d '{
    "tool": "nmap",
    "target": "example.com",
    "options": ["-sV"]
  }'
```

## Docker Sandbox

Tools run in isolated Docker containers:

```python
from tools.docker_sandbox import DockerSandbox

sandbox = DockerSandbox(
    image="zen-pentest-tools:latest",
    timeout=300,
    network="sandbox"
)

result = await sandbox.run(
    command="nmap -sV example.com",
    read_only=True  # No write access
)
```

## Safety Controls

### Private IP Blocking

```python
# Automatically blocks:
# - 10.0.0.0/8
# - 172.16.0.0/12
# - 192.168.0.0/16
# - 127.0.0.0/8
```

### Timeout Management

```python
# Default: 10 minutes
# Customizable:
executor = ToolExecutor(timeout=600)
```

### Resource Limits

```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
```

## Output Formats

| Format | Description |
|--------|-------------|
| JSON | Machine readable |
| XML | For integration |
| HTML | For reports |
| PDF | For customers |

## Adding New Tools

### 1. Tool Definition

```python
# tools/custom/my_tool.py
from tools.base import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "My custom tool"

    async def run(self, target, options=None):
        # Implementation
        return {"result": "..."}
```

### 2. Register

```python
# tools/registry.py
from tools.custom.my_tool import MyTool

registry.register(MyTool())
```

### 3. Test

```bash
python3 -m pytest tests/tools/test_my_tool.py
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Zen-AI-Pentest Scan
  uses: SHAdd0WTAka/zen-ai-pentest@main
  with:
    target: ${{ vars.TARGET_URL }}
    scan-type: 'recon'
    output-format: 'sarif'
```

### GitLab CI

```yaml
zen-scan:
  image: zen-ai-pentest:latest
  script:
    - zen-cli scan --target $TARGET --output results.json
  artifacts:
    reports:
      sast: results.json
```

### Jenkins

```groovy
pipeline {
    agent { docker 'zen-ai-pentest:latest' }
    stages {
        stage('Security Scan') {
            steps {
                sh 'zen-cli scan --target example.com'
            }
        }
    }
}
```

## Plugins

Zen-AI-Pentest supports a plugin system:

```python
# plugins/my_plugin.py
from core.plugins import BasePlugin

class MyPlugin(BasePlugin):
    name = "my_plugin"

    def on_scan_start(self, scan):
        print(f"Scan started: {scan.id}")

    def on_scan_complete(self, scan, results):
        print(f"Scan completed: {scan.id}")
```

---

*For the complete list of all 72+ tools, see [Tools-Complete-List.md](Tools-Complete-List.md)*
