# Tools & Integration

Zen-AI-Pentest integriert 40+ professionelle Security-Tools.

## Integrierte Tools

### Reconnaissance

| Tool | Zweck | Sicherheitsstufe |
|------|-------|-----------------|
| Nmap | Port Scanning | ✅ Safe |
| Subfinder | Subdomain Enum | ✅ Safe |
| HTTPX | HTTP Probing | ✅ Safe |
| Whois | Domain Info | ✅ Safe |
| Dig | DNS Queries | ✅ Safe |

### Vulnerability Scanning

| Tool | Zweck | Sicherheitsstufe |
|------|-------|-----------------|
| Nuclei | CVE Detection | ✅ Safe |
| Nikto | Web Scanner | ✅ Safe |
| SQLMap | SQL Injection | ⚠️ Medium |
| WAFW00F | WAF Detection | ✅ Safe |
| WhatWeb | Tech Detection | ✅ Safe |

### Exploitation

| Tool | Zweck | Sicherheitsstufe |
|------|-------|-----------------|
| Metasploit | Exploitation | ⚠️ High |
| SQLMap | SQL Injection | ⚠️ Medium |
| FFuF | Web Fuzzing | ✅ Safe |

### Brute Force

| Tool | Zweck | Sicherheitsstufe |
|------|-------|-----------------|
| Hydra | Login Brute | ⚠️ Medium |
| John | Password Crack | ✅ Safe |
| Hashcat | Password Crack | ✅ Safe |

## Tool Ausführung

### Direkt

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

Tools laufen in isolierten Docker-Containern:

```python
from tools.docker_sandbox import DockerSandbox

sandbox = DockerSandbox(
    image="zen-pentest-tools:latest",
    timeout=300,
    network="sandbox"
)

result = await sandbox.run(
    command="nmap -sV example.com",
    read_only=True  # Keine Schreibzugriffe
)
```

## Safety Controls

### Private IP Blocking

```python
# Blockiert automatisch:
# - 10.0.0.0/8
# - 172.16.0.0/12
# - 192.168.0.0/16
# - 127.0.0.0/8
```

### Timeout Management

```python
# Standard: 10 Minuten
# Anpassbar:
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

## Output Formate

| Format | Beschreibung |
|--------|--------------|
| JSON | Maschinenlesbar |
| XML | Für Integration |
| HTML | Für Reports |
| PDF | Für Kunden |

## Neue Tools hinzufügen

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

### 2. Registrieren

```python
# tools/registry.py
from tools.custom.my_tool import MyTool

registry.register(MyTool())
```

### 3. Testen

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

Zen-AI-Pentest unterstützt ein Plugin-System:

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
