# Container Integration Guide

Zen AI Pentest can be deployed as part of a comprehensive containerized pentesting pipeline, integrating with classic security tools like **Nmap**, **Metasploit**, **SQLMap**, **Nuclei**, and many more.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Zen Pentest Stack                        │
├─────────────────────────────────────────────────────────────┤
│  zen-core          │  Main AI orchestrator & analysis       │
│  integration-bridge│  API gateway for tool communication    │
├─────────────────────────────────────────────────────────────┤
│  nmap              │  Port scanner with NSE scripts         │
│  nuclei            │  Fast vulnerability scanner            │
│  sqlmap            │  SQL injection testing                 │
│  metasploit        │  Exploitation framework                │
│  gobuster          │  Directory/file bruteforcer            │
│  amass             │  Subdomain enumeration                 │
│  wpscan            │  WordPress vulnerability scanner       │
│  nikto             │  Web server scanner                    │
│  masscan           │  High-speed port scanner               │
│  openvas (opt)     │  Vulnerability scanner                 │
├─────────────────────────────────────────────────────────────┤
│  redis             │  Caching & task queue                  │
│  postgres          │  Data persistence                      │
│  results-ui        │  Web interface for results             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Start the Full Stack

```bash
# Start all services
docker-compose -f docker-compose.pentest.yml up -d

# Check status
docker-compose -f docker-compose.pentest.yml ps

# View logs
docker-compose -f docker-compose.pentest.yml logs -f
```

### 2. Verify Bridge API

```bash
curl http://localhost:8080/health
```

### 3. Run Your First Scan

```bash
# Nmap scan
python integration/cli.py nmap scanme.nmap.org

# Or use the API directly
curl -X POST http://localhost:8080/api/v1/scan/nmap \
  -H "Content-Type: application/json" \
  -d '{
    "target": "scanme.nmap.org",
    "scan_type": "tcp_syn",
    "ports": "top-1000"
  }'
```

## 📋 Available Tools

### Network Scanning

| Tool | Purpose | Example |
|------|---------|---------|
| **Nmap** | Port scanning | `cli.py nmap 192.168.1.1 --type comprehensive` |
| **Masscan** | High-speed scanning | Via API endpoint |
| **Amass** | Subdomain enum | `cli.py amass example.com` |

### Web Application Testing

| Tool | Purpose | Example |
|------|---------|---------|
| **Nuclei** | Vulnerability scanning | `cli.py nuclei https://example.com` |
| **SQLMap** | SQL injection | `cli.py sqlmap "http://test.com?id=1"` |
| **Gobuster** | Directory brute | `cli.py gobuster https://example.com` |
| **WPScan** | WordPress scan | `cli.py wpscan https://wp-site.com` |
| **Nikto** | Web server scan | Via API endpoint |

### Exploitation

| Tool | Purpose | Example |
|------|---------|---------|
| **Metasploit** | Exploitation | Via API with module specification |
| **OpenVAS** | Vulnerability mgmt | Access via port 9392 |

## 🔧 API Endpoints

### Scan Endpoints

```http
POST   /api/v1/scan/nmap         # Port scanning
POST   /api/v1/scan/sqlmap       # SQL injection testing
POST   /api/v1/scan/nuclei       # Vulnerability scanning
POST   /api/v1/scan/metasploit   # Exploitation modules
POST   /api/v1/scan/gobuster     # Directory enumeration
POST   /api/v1/scan/amass        # Subdomain discovery
POST   /api/v1/scan/wpscan       # WordPress scanning
POST   /api/v1/scan/nikto        # Web server scanning
```

### Management Endpoints

```http
GET    /api/v1/scan/{scan_id}           # Scan status
GET    /api/v1/scan/{scan_id}/results   # Scan results
GET    /api/v1/scans                    # List all scans
DELETE /api/v1/scan/{scan_id}          # Cancel scan
GET    /health                          # Health check
```

## 💻 Python Integration

### Basic Usage

```python
from modules.tool_orchestrator import ToolOrchestrator

async with ToolOrchestrator("http://localhost:8080") as orch:
    # Run Nmap scan
    result = await orch.scan_with_nmap("target.com")
    scan_id = result['scan_id']

    # Wait for completion
    status = await orch.wait_for_scan(scan_id)

    # Get results
    results = await orch.get_scan_results(scan_id)
```

### Comprehensive Scan

```python
# Run multiple tools automatically
results = await orch.run_comprehensive_scan(
    target="example.com",
    scan_type="web"  # web, network, or full
)

# Display summary
orch.display_scan_summary(results)
```

### Concurrent Scans

```python
import asyncio

# Run multiple scans in parallel
nmap_task = orch.scan_with_nmap("target.com")
nuclei_task = orch.scan_with_nuclei("https://target.com")
amass_task = orch.enumerate_subdomains("target.com")

results = await asyncio.gather(
    nmap_task,
    nuclei_task,
    amass_task,
    return_exceptions=True
)
```

## 🐳 Docker Compose Profiles

### Standard Profile (Default)

Core tools for most pentests:
- zen-core, integration-bridge
- nmap, nuclei, sqlmap
- gobuster, amass
- redis, postgres

```bash
docker-compose -f docker-compose.pentest.yml up -d
```

### Full Profile

Includes resource-intensive tools:
```bash
docker-compose -f docker-compose.pentest.yml --profile full-scan up -d
```

This adds:
- OpenVAS (Vulnerability management)

## 📁 Shared Volumes

| Volume | Path | Purpose |
|--------|------|---------|
| `shared-scans` | `/shared/scans` | Raw scan outputs |
| `shared-reports` | `/shared/reports` | Generated reports |
| `evidence` | `/evidence` | Evidence collection |
| `wordlists` | `/wordlists` | Wordlist storage |

Access via web UI: http://localhost:8081

## 🔐 Security Considerations

### Network Isolation

- **pentest-network**: External-facing tools
- **internal-network**: Internal services (Redis, Postgres)

### Capabilities

Tools requiring raw sockets have specific capabilities:
```yaml
cap_add:
  - NET_RAW
  - NET_ADMIN
```

### Safe Testing

Always use authorized targets:
- `scanme.nmap.org` - Nmap's test server
- `testphp.vulnweb.com` - Acunetix test site
- Your own infrastructure

## 🛠️ Customization

### Adding Custom NSE Scripts

Mount your scripts:
```yaml
volumes:
  - ./custom-scripts:/usr/share/nmap/scripts/custom
```

### Custom Wordlists

Add to the wordlists volume:
```bash
docker cp my-wordlist.txt zen-wordlists:/wordlists/custom/
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ZEN_MODE` | Operation mode | `orchestrator` |
| `ZEN_LOG_LEVEL` | Logging level | `INFO` |
| `REDIS_URL` | Redis connection | `redis://redis:6379/0` |
| `POSTGRES_URL` | Database URL | `postgresql://...` |

## 📊 Monitoring

### Check Active Scans

```bash
# Via API
curl http://localhost:8080/api/v1/scans

# Via Docker
docker-compose -f docker-compose.pentest.yml top
```

### View Logs

```bash
# All services
docker-compose -f docker-compose.pentest.yml logs -f

# Specific service
docker-compose -f docker-compose.pentest.yml logs -f nmap
```

## 🧪 Examples

### Example 1: Network Reconnaissance

```python
async def network_recon(target):
    async with ToolOrchestrator() as orch:
        # Port scan
        nmap = await orch.scan_with_nmap(target, "comprehensive")
        await orch.wait_for_scan(nmap['scan_id'])

        # Subdomain enumeration
        amass = await orch.enumerate_subdomains(target)
        await orch.wait_for_scan(amass['scan_id'])

        return await orch.get_scan_results(nmap['scan_id'])
```

### Example 2: Web Application Test

```python
async def web_app_test(url):
    async with ToolOrchestrator() as orch:
        # Directory enumeration
        gobuster = await orch.scan_with_gobuster(url)

        # Vulnerability scan
        nuclei = await orch.scan_with_nuclei(url, severity="high,critical")

        # SQL injection
        sqlmap = await orch.scan_with_sqlmap(url, level=2, risk=1)

        # Wait for all
        await asyncio.gather(
            orch.wait_for_scan(gobuster['scan_id']),
            orch.wait_for_scan(nuclei['scan_id']),
            orch.wait_for_scan(sqlmap['scan_id'])
        )
```

### Example 3: CI/CD Integration

```yaml
# .github/workflows/pentest.yml
- name: Run Security Scan
  run: |
    docker-compose -f docker-compose.pentest.yml up -d
    sleep 10
    python integration/cli.py comprehensive https://staging.example.com
```

## 🐛 Troubleshooting

### Bridge Connection Refused

```bash
# Check if bridge is running
docker-compose -f docker-compose.pentest.yml ps integration-bridge

# Restart bridge
docker-compose -f docker-compose.pentest.yml restart integration-bridge
```

### Scan Timeouts

Increase timeout in your code:
```python
await orch.wait_for_scan(scan_id, timeout=7200)  # 2 hours
```

### Permission Denied

Check Docker socket permissions:
```bash
sudo chmod 666 /var/run/docker.sock
```

## 📚 Further Reading

- [Nmap Documentation](https://nmap.org/book/)
- [SQLMap Usage](https://github.com/sqlmapproject/sqlmap/wiki/Usage)
- [Nuclei Templates](https://docs.projectdiscovery.io/templates/)
- [Metasploit Framework](https://docs.metasploit.com/)

## 🤝 Contributing

To add a new tool:

1. Add service to `docker-compose.pentest.yml`
2. Create endpoint in `integration/bridge.py`
3. Add orchestrator method in `modules/tool_orchestrator.py`
4. Update CLI in `integration/cli.py`
5. Document in this guide
