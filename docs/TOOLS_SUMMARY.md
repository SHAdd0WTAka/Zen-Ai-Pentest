# Pentesting Tools Integration - Zusammenfassung

## Übersicht

Zen-AI-Pentest integriert nun **20+ professionelle Pentesting-Tools** für comprehensive Security-Assessments.

---

## Implementierte Tools

### 1. Netzwerk-Scanning (6 Tools)

| Tool | Zweck | LangChain Tool |
|------|-------|----------------|
| **Nmap** | Port-Scanning, OS Detection | `nmap_scan` |
| **Masscan** | Ultra-schneller Async-Scan | `masscan_quick_scan` |
| **Scapy** | Python-Paket-Manipulation | `scapy_syn_scan`, `scapy_arp_scan` |
| **Tshark** | Headless Wireshark-Analyse | `tshark_capture`, `tshark_analyze_pcap` |

### 2. Web-Anwendungen (4 Tools)

| Tool | Zweck | LangChain Tool |
|------|-------|----------------|
| **BurpSuite** | Web-Proxy, Scanner | `burp_scan_url` |
| **SQLMap** | SQL-Injection-Exploitation | `sqlmap_scan` |
| **Gobuster** | Directory/File Busting | `gobuster_dir_scan`, `gobuster_dns_scan` |

### 3. Exploitation (2 Tools)

| Tool | Zweck | LangChain Tool |
|------|-------|----------------|
| **Metasploit** | Exploit-Framework | `metasploit_search`, `msfvenom_generate` |

### 4. Brute-Force (2 Tools)

| Tool | Zweck | LangChain Tool |
|------|-------|----------------|
| **Hydra** | Online Password Cracking | `hydra_ssh_brute`, `hydra_ftp_brute` |

### 5. Reconnaissance (2 Tools)

| Tool | Zweck | LangChain Tool |
|------|-------|----------------|
| **Amass** | Subdomain-Enumeration | `amass_enum` |
| **Nuclei** | Vulnerability-Scanner | (bereits implementiert) |

### 6. Active Directory / Windows (3 Tools)

| Tool | Zweck | LangChain Tool |
|------|-------|----------------|
| **BloodHound** | AD-Attack-Path-Analyse | `bloodhound_analyze_path` |
| **CrackMapExec** | SMB/WinRM/LDAP Swiss Army Knife | `cme_smb_check` |
| **Responder** | LLMNR/NBT-NS Poisoning | `responder_analyze` |

### 7. Wireless Security (1 Tool)

| Tool | Zweck | LangChain Tool |
|------|-------|----------------|
| **Aircrack-ng** | WiFi Security Testing | `airodump_scan`, `aircrack_wpa` |

---

## Tool-Verwendung im Agent

### Einfacher Aufruf

```python
from tools import TOOL_REGISTRY

# Tool direkt aufrufen
result = TOOL_REGISTRY['nmap_scan'](target="scanme.nmap.org", ports="22,80,443")
print(result)
```

### Im ReAct Agent

```python
from agents.react_agent import ReActAgent
from tools import get_all_tools

# Alle Tools laden
tools = get_all_tools()

# Agent mit Tools erstellen
agent = ReActAgent()
agent.tools = tools

# Autonomer Scan
result = agent.run("scanme.nmap.org", "Comprehensive security scan")
```

---

## Cloud & VM Integration

### Unterstützte Plattformen

| Plattform | Status | Features |
|-----------|--------|----------|
| **VirtualBox** | ✅ Vollständig | Local VMs, Snapshots, Guest Control |
| **AWS EC2** | ✅ Implementiert | Kali-AMI, Auto-Shutdown |
| **Azure VMs** | ✅ Implementiert | Multi-Region, Snapshots |
| **GCP Compute** | ✅ Implementiert | Custom Images |

### Cloud-Manager

```python
from virtualization.cloud_vm_manager import create_aws_manager

# AWS Manager
manager = create_aws_manager('AKIA...', 'secret...', 'us-east-1')

# Kali-Instanz erstellen
instance_id = manager.create_kali_instance('aws', 'us-east-1')

# Tools ausführen
exit_code, stdout, stderr = manager.execute_ssh_command(
    instance_id, "nmap -sV target.com", "/path/to/key.pem"
)
```

---

## GUI für VM-Management

### Web-Interface

```bash
# GUI starten
python gui/vm_manager_gui.py

# Oder
python -m gui.vm_manager_gui
```

Zugriff: http://localhost:8080

### Features

- 📊 VM-Status Dashboard
- ▶️ Start/Stop/Reset Controls
- 💾 Snapshot Management
- ☁️ Multi-Cloud Support
- 📜 Live-Logs

---

## Installation der Tools

### Kali Linux (empfohlen)

```bash
# Alle Tools sind vorinstalliert auf Kali
sudo apt update
sudo apt install -y \
    nmap masscan sqlmap gobuster hydra \
    tshark wireshark burpsuite metasploit-framework \
    amass bloodhound crackmapexec responder \
    aircrack-ng

# Python-Pakete
pip install scapy pyshark
```

### Andere Distributionen

```bash
# Ubuntu/Debian
sudo apt install nmap sqlmap gobuster

# macOS
brew install nmap sqlmap masscan

# Python-Tools
pip install -r requirements.txt
```

---

## Tool-Kategorien

```
┌─────────────────────────────────────────────────────────────┐
│                    ZEN-AI-PENTEST                           │
├─────────────────────────────────────────────────────────────┤
│  NETWORK LAYER          WEB LAYER         SYSTEM LAYER      │
│  ─────────────          ─────────         ────────────      │
│  • Nmap                 • BurpSuite       • Metasploit      │
│  • Masscan              • SQLMap          • Hydra           │
│  • Scapy                • Gobuster        • CME             │
│  • Tshark                                         │
│                                                      │
│  RECONNAISSANCE         WIRELESS            AD/ENTERPRISE   │
│  ──────────────         ────────            ─────────────   │
│  • Amass                • Aircrack-ng       • BloodHound    │
│  • Nuclei                                   • Responder     │
│  • TheHarvester                             • CME           │
│                                                      │
│  INFRASTRUCTURE: VirtualBox, AWS, Azure, GCP              │
└─────────────────────────────────────────────────────────────┘
```

---

## Nächste Schritte

1. **Tool-Ausführung testen**: `python -m tools.nmap_integration`
2. **VM Setup**: `python scripts/setup_vms.py --kali`
3. **GUI starten**: `python gui/vm_manager_gui.py`
4. **Agent mit Tools**: Siehe `examples/react_agent_example.py`

---

## Ressourcen

- Tool-Dokumentationen in `docs/research/FUNDAMENTAL_PENTEST_TOOLS.md`
- Beispiele in `examples/`
- API-Referenz in `tools/__init__.py`

---

### 8. Web Application Security (1 Tool)

| Tool | Zweck | LangChain Tool |
|------|-------|----------------|
| **OWASP ZAP** | Web Application Security Scanner | `zap_scan_url`, `zap_quick_scan`, `zap_spider_only` |

**Features:**
- Spider/Crawl functionality
- Active scanning with policies
- AJAX spider for modern web apps
- API scan support
- Report generation (HTML, XML, JSON)
- Async scanning with progress callbacks

**Setup:**
```bash
# Install ZAP
wget https://github.com/zaproxy/zaproxy/releases/download/v2.14.0/ZAP_2_14_0_unix.sh
chmod +x ZAP_2_14_0_unix.sh
sudo ./ZAP_2_14_0_unix.sh

# Or use Docker
docker pull ghcr.io/zaproxy/zaproxy:stable
```

**Usage:**
```python
from tools.zap_integration import ZAPScanner

# Start ZAP daemon first
scanner = ZAPScanner(
    target="http://example.com",
    api_url="http://localhost:8080",
    options={"spider": True, "active_scan": True}
)
result = await scanner.scan()
```

---

### 9. Secrets Detection (1 Tool)

| Tool | Zweck | LangChain Tool |
|------|-------|----------------|
| **TruffleHog** | Secrets Detection in Code | `trufflehog_scan_git`, `trufflehog_scan_path` |

**Features:**
- Git repository scanning
- Filesystem scanning
- Verified secrets only option
- Custom regex patterns
- Multiple output formats
- Severity classification

**Setup:**
```bash
# Install TruffleHog
pip install trufflehog
# Or download binary from GitHub releases
```

**Usage:**
```python
from tools.trufflehog_integration import TruffleHogScanner

scanner = TruffleHogScanner(verified_only=True)

# Scan git repository
result = await scanner.scan_git("https://github.com/user/repo")

# Scan filesystem
result = await scanner.scan_filesystem("/path/to/code")
```

---

### 10. Cloud Security (1 Tool)

| Tool | Zweck | LangChain Tool |
|------|-------|----------------|
| **ScoutSuite** | Cloud Security Posture Assessment | `scoutsuite_scan_aws`, `scoutsuite_scan_azure`, `scoutsuite_scan_gcp` |

**Features:**
- AWS, Azure, GCP support
- Compliance checking (CIS, PCI-DSS, HIPAA, GDPR)
- Security rule evaluation
- Report parsing and normalization
- Risk scoring integration

**Setup:**
```bash
# Install ScoutSuite
pip install scoutsuite

# Configure cloud credentials
aws configure
az login
gcloud auth application-default login
```

**Usage:**
```python
from tools.scout_integration import ScoutSuiteScanner, CloudProvider

scanner = ScoutSuiteScanner(
    provider=CloudProvider.AWS,
    regions=["us-east-1"],
    services=["iam", "s3", "ec2"]
)
result = await scanner.scan()
```

---

### 11. Container Security (1 Tool)

| Tool | Zweck | LangChain Tool |
|------|-------|----------------|
| **Trivy** | Container and Filesystem Scanner | `trivy_scan_image`, `trivy_scan_filesystem`, `trivy_generate_sbom` |

**Features:**
- Container image scanning
- Filesystem scanning
- SBOM generation
- CVE detection
- Misconfiguration detection
- Secret detection

**Setup:**
```bash
# Install Trivy
sudo apt-get install trivy
# Or
docker pull aquasec/trivy:latest
```

**Usage:**
```python
from tools.trivy_integration import TrivyScanner, TrivyScannerType

scanner = TrivyScanner(
    severity=["HIGH", "CRITICAL"],
    scanners=[TrivyScannerType.VULNERABILITY, TrivyScannerType.MISCONFIGURATION]
)

# Scan image
result = await scanner.scan_image("nginx:latest")

# Scan filesystem
result = await scanner.scan_filesystem("/path/to/code")

# Generate SBOM
sbom = await scanner.generate_sbom("nginx:latest")
```

---

### 12. Static Code Analysis (1 Tool)

| Tool | Zweck | LangChain Tool |
|------|-------|----------------|
| **Semgrep** | Static Analysis for Code Security | `semgrep_scan_code`, `semgrep_scan_owasp`, `semgrep_scan_secrets` |

**Features:**
- Custom rule support
- OWASP/CWE coverage
- Multiple language support
- CI/CD integration
- Finding categorization
- False positive handling

**Setup:**
```bash
# Install Semgrep
pip install semgrep
# Or
docker pull returntocorp/semgrep:latest
```

**Usage:**
```python
from tools.semgrep_integration import SemgrepScanner

scanner = SemgrepScanner(
    config=["p/security-audit", "p/owasp-top-ten", "p/cwe-top-25"]
)

result = await scanner.scan("/path/to/code")

# Or use specific rule sets
scanner.add_owasp_rules()
scanner.add_secrets_rules()
```

---

## New Tools Demo

### Quick Start

```bash
# Run the new tools demo
python examples/new_tools_demo.py
```

### Individual Tool Examples

```python
# OWASP ZAP
from tools.zap_integration import zap_quick_scan
result = zap_quick_scan("http://example.com")

# TruffleHog
from tools.trufflehog_integration import trufflehog_scan_git
result = trufflehog_scan_git("https://github.com/user/repo")

# ScoutSuite
from tools.scout_integration import scoutsuite_scan_aws
result = scoutsuite_scan_aws(profile="production")

# Trivy
from tools.trivy_integration import trivy_scan_image
result = trivy_scan_image("nginx:latest")

# Semgrep
from tools.semgrep_integration import semgrep_scan_owasp
result = semgrep_scan_owasp("/path/to/code")
```

---

## Tool-Kategorien (Aktualisiert)

```
┌─────────────────────────────────────────────────────────────────┐
│                    ZEN-AI-PENTEST                               │
├─────────────────────────────────────────────────────────────────┤
│  NETWORK LAYER          WEB LAYER           SYSTEM LAYER        │
│  ─────────────          ─────────           ────────────        │
│  • Nmap                 • BurpSuite         • Metasploit        │
│  • Masscan              • SQLMap            • Hydra             │
│  • Scapy                • Gobuster          • CME               │
│  • Tshark               • OWASP ZAP                             │
│                                                                 │
│  CODE SECURITY          CONTAINER           CLOUD               │
│  ─────────────          ─────────           ─────               │
│  • Semgrep              • Trivy             • ScoutSuite        │
│  • TruffleHog                                                   │
│                                                                 │
│  RECONNAISSANCE         WIRELESS            AD/ENTERPRISE       │
│  ──────────────         ────────            ─────────────       │
│  • Amass                • Aircrack-ng       • BloodHound        │
│  • Nuclei                                   • Responder         │
│  • TruffleHog                               • CME               │
│                                                                 │
│  INFRASTRUCTURE: VirtualBox, AWS, Azure, GCP                    │
└─────────────────────────────────────────────────────────────────┘
```

---

**Status**: ✅ 25+ Tools implementiert und integriert
