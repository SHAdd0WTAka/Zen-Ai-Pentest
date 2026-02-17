# 🔧 Enhanced Tools Integration

Dieses Dokument beschreibt die neuen Tool-Integrationen in Zen-AI-Pentest v2.3.9+

---

## 🎯 Neue Tools Übersicht

| Tool | Kategorie | Zweck | Status |
|------|-----------|-------|--------|
| **FFuF** | Fuzzing | Directory/Parameter Bruteforce | ✅ |
| **WhatWeb** | Enumeration | Technology Detection | ✅ |
| **WAFW00F** | Detection | WAF Erkennung | ✅ |
| **Subfinder** | Reconnaissance | Subdomain Discovery | ✅ |
| **HTTPX** | Probing | Fast HTTP Probing | ✅ |
| **Nikto** | Scanning | Web Vulnerability Scanner | ✅ |

---

## 🚀 Schnellstart

### Enhanced Recon Module

```python
from modules.enhanced_recon import EnhancedReconModule

recon = EnhancedReconModule()
result = recon.full_recon("example.com")

# Ergebnisse
print(f"Technologien: {result['summary']['technologies_found']}")
print(f"WAF erkannt: {result['summary']['waf_detected']}")
print(f"Directories: {result['summary']['directories_found']}")
print(f"Risk Level: {result['summary']['risk_level']}")
```

### CLI Usage

```bash
# Full reconnaissance
python -m modules.enhanced_recon --target example.com

# Technology detection only
python -m modules.enhanced_recon --target example.com --mode tech

# WAF detection only
python -m modules.enhanced_recon --target example.com --mode waf

# Directory bruteforce
python -m modules.enhanced_recon --target example.com --mode dir -e php,html,txt
```

---

## 📊 Tool Details

### 1. FFuF Integration

**Features:**
- ⚡ Blazing fast directory discovery
- 🔍 Parameter fuzzing
- 🌐 Virtual host discovery
- 📊 JSON output parsing

**Usage:**
```python
from tools.ffuf_integration_enhanced import directory_bruteforce_sync

result = directory_bruteforce_sync(
    "http://example.com/FUZZ",
    extensions=["php", "html", "txt"],
    wordlist="/usr/share/wordlists/dirb/common.txt"
)

for finding in result.findings:
    print(f"[{finding.status_code}] {finding.url}")
```

### 2. WhatWeb Integration

**Features:**
- 🎯 CMS Detection (900+ Plugins)
- 🔧 Framework Detection
- 📱 Technology Stack Identification
- 🏷️ Version Extraction

**Usage:**
```python
from tools.whatweb_integration import scan_sync

result = scan_sync("http://example.com")

for tech in result.technologies:
    print(f"{tech.name} {tech.version} [{tech.category}]")
```

**Beispiel Output:**
```
Apache 2.4.41 [Web Server]
PHP 7.4.3 [Programming Language]
WordPress 5.8.1 [CMS]
jQuery 3.6.0 [JavaScript Library]
```

### 3. WAFW00F Integration

**Features:**
- 🛡️ 50+ WAFs erkennbar
- ☁️ Cloud WAFs (Cloudflare, AWS, etc.)
- 🏢 Enterprise WAFs (F5, Imperva, etc.)
- 📊 Confidence Scoring

**Usage:**
```python
from tools.wafw00f_integration import detect_sync

result = detect_sync("http://example.com")

if result.firewall_detected:
    for waf in result.wafs:
        print(f"WAF: {waf.name} ({waf.confidence})")
```

### 4. Subfinder Integration

**Features:**
- 🌐 Passive Subdomain Enumeration
- 🔄 Recursive Discovery
- 📊 JSON Output
- ⚡ High Performance

**Usage:**
```python
from tools.subfinder_integration import enumerate_sync

result = enumerate_sync("example.com", recursive=True)

print(f"Found {result.count} subdomains:")
for subdomain in result.subdomains[:10]:
    print(f"  • {subdomain}")
```

### 5. HTTPX Integration

**Features:**
- ⚡ Fast HTTP Probing (1000+ req/s)
- 🎯 Multi-target Support
- 📊 Technology Detection
- 🔄 Redirect Following

**Usage:**
```python
from tools.httpx_integration import probe_sync

targets = ["example.com", "www.example.com", "api.example.com"]
result = probe_sync(targets)

for host in result.hosts:
    print(f"{host.url} - {host.status_code} - {host.title}")
```

### 6. Nikto Integration

**Features:**
- 🔍 6700+ Vulnerability Tests
- 📁 Dangerous Files Detection
- 🔧 Configuration Issues
- 🌐 Web Server Misconfigurations

**Usage:**
```python
from tools.nikto_integration import scan_sync

result = scan_sync("http://example.com", ssl=True)

for finding in result.findings:
    print(f"[{finding.severity}] {finding.id}: {finding.description}")
```

---

## 🔧 Installation

### Kali Linux

```bash
# System packages
sudo apt-get update
sudo apt-get install -y ffuf whatweb wafw00f nikto

# ProjectDiscovery Tools
cd ~/tools

# Subfinder
wget https://github.com/projectdiscovery/subfinder/releases/latest/download/subfinder_linux_amd64.zip
unzip subfinder_linux_amd64.zip
sudo mv subfinder /usr/local/bin/

# HTTPX
wget https://github.com/projectdiscovery/httpx/releases/latest/download/httpx_linux_amd64.zip
unzip httpx_linux_amd64.zip
sudo mv httpx /usr/local/bin/

# Verify installations
which ffuf whatweb wafw00f subfinder httpx nikto
```

---

## 🧪 Tests

```bash
# Run all enhanced tool tests
pytest tests/test_enhanced_tools.py -v

# Run specific test class
pytest tests/test_enhanced_tools.py::TestFFuFIntegration -v

# Run with coverage
pytest tests/test_enhanced_tools.py --cov=tools --cov-report=html
```

---

## 📈 Beispiel-Workflow

```python
import asyncio
from modules.enhanced_recon import EnhancedReconModule
from tools.subfinder_integration import enumerate_sync
from tools.httpx_integration import probe_sync

async def comprehensive_scan(domain):
    """Comprehensive reconnaissance workflow"""
    
    # Phase 1: Subdomain Enumeration
    print("[*] Enumerating subdomains...")
    subdomains = enumerate_sync(domain, recursive=True)
    targets = subdomains.subdomains[:50]  # Top 50
    
    # Phase 2: HTTP Probing
    print("[*] Probing live hosts...")
    live_hosts = probe_sync(targets)
    
    # Phase 3: Deep Recon on each live host
    print("[*] Running deep recon...")
    recon = EnhancedReconModule()
    
    results = []
    for host in live_hosts.hosts:
        if host.status_code == 200:
            result = recon.full_recon(host.url)
            results.append(result)
    
    return results

# Run scan
results = asyncio.run(comprehensive_scan("example.com"))
```

---

## 🔒 Safety Controls

Alle Tools haben integrierte Safety Controls:

| Control | Implementierung |
|---------|----------------|
| Timeout | 60-300s je nach Tool |
| Rate Limiting | Konfigurierbar (default: 50 req/s) |
| Private IP Blocking | Automatisch |
| Scope Validation | Target Whitelist |

---

## 🤝 Integration in Zen-AI-Pentest

Die neuen Tools sind nahtlos in das Framework integriert:

```
Zen-AI-Pentest/
├── modules/
│   └── enhanced_recon.py     # Kombiniert alle Tools
├── tools/
│   ├── ffuf_integration_enhanced.py
│   ├── whatweb_integration.py
│   ├── wafw00f_integration.py
│   ├── subfinder_integration.py
│   ├── httpx_integration.py
│   └── nikto_integration.py
└── tests/
    └── test_enhanced_tools.py
```

---

## 📚 Weitere Dokumentation

- [Tools Integration Guide](TOOLS_INTEGRATION_GUIDE.md)
- [API Documentation](docs/API.md)
- [Architecture Overview](docs/ARCHITECTURE.md)

---

*Last Updated: 2026-02-17*
*Version: 2.3.9+*
