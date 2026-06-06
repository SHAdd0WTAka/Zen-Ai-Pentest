# 🔧 Neue Tool-Integrationen

Dieses Dokument beschreibt die neuen Tool-Integrationen für das Zen-AI-Pentest Framework.

## 📋 Übersicht

| Tool | Zweck | Datei | Status |
|------|-------|-------|--------|
| **FFuF** | Directory/Parameter Fuzzing | `tools/ffuf_integration_enhanced.py` | ✅ Ready |
| **WhatWeb** | Technology Detection | `tools/whatweb_integration.py` | ✅ Ready |
| **WAFW00F** | WAF Detection | `tools/wafw00f_integration.py` | ✅ Ready |
| **Unified Scanner** | Kombination aller Tools | `tools/unified_recon.py` | ✅ Ready |

---

## 🚀 Quick Start

### 1. Unified Scanner (Empfohlen)

```bash
cd tools
python unified_recon.py --target example.com
```

**Output:**
- Technology Detection (Apache, nginx, etc.)
- WAF Detection (Cloudflare, AWS WAF, etc.)
- Directory Bruteforce
- JSON Report
- Sicherheitsempfehlungen

### 2. Einzelne Tools nutzen

**FFuF - Directory Bruteforce:**
```python
from tools.ffuf_integration_enhanced import directory_bruteforce_sync

result = directory_bruteforce_sync(
    "http://example.com/FUZZ",
    extensions=["php", "html", "txt"]
)

for finding in result.findings:
    print(f"[{finding.status_code}] {finding.url}")
```

**WhatWeb - Technology Detection:**
```python
from tools.whatweb_integration import scan_sync

result = scan_sync("http://example.com")

for tech in result.technologies:
    print(f"{tech.name} {tech.version}")
```

**WAFW00F - WAF Detection:**
```python
from tools.wafw00f_integration import detect_sync

result = detect_sync("http://example.com")

if result.firewall_detected:
    for waf in result.wafs:
        print(f"WAF: {waf.name}")
```

---

## 📊 Tool Details

### FFuF Integration

**Features:**
- Directory Bruteforce
- Parameter Fuzzing
- Virtual Host Discovery
- JSON Output Parsing
- Async/await Support

**Methoden:**
- `directory_bruteforce()` - Verzeichnisse aufdecken
- `parameter_fuzzing()` - Parameter testen
- `vhost_discovery()` - Virtuelle Hosts finden

### WhatWeb Integration

**Features:**
- CMS Detection (WordPress, Drupal, Joomla)
- Framework Detection (React, Angular, jQuery)
- Server Detection (Apache, nginx, IIS)
- Version Extraction
- Confidence Scoring

**Methoden:**
- `scan()` - Technologie-Scan

### WAFW00F Integration

**Features:**
- WAF Erkennung (50+ WAFs)
- Cloudflare, AWS WAF, ModSecurity, etc.
- Confidence Level

**Methoden:**
- `detect()` - WAF Detection

---

## 🎯 Verwendung im Framework

### Integration in bestehende Workflows

```python
from tools.unified_recon import UnifiedReconScanner

scanner = UnifiedReconScanner()
result = asyncio.run(scanner.run_full_scan("example.com"))

# Zugriff auf Ergebnisse
techs = result.technology_scan
directories = result.directory_bruteforce
waf = result.waf_detection
```

### Report Generierung

```python
# Automatische Reports
scanner.save_report(result)

# Manuelle Ausgabe
scanner.print_report(result)
```

---

## 📈 Beispiel-Output

```
🎯 UNIFIED RECONNAISSANCE REPORT
======================================================================
Target: scanme.nmap.org
Timestamp: 2026-02-17T05:06:10

📊 TECHNOLOGY DETECTION
----------------------------------------------------------------------
Found 5 technologies:
  • Apache [2.4.7] [100%]
  • Ubuntu Linux [100%]
  • Google-Analytics [Universal] [100%]
  • HTML5 [100%]

🛡️  WAF DETECTION
----------------------------------------------------------------------
✅ No WAF detected

📁 DIRECTORY BRUTEFORCE
----------------------------------------------------------------------
Found 3 accessible paths:
  [200] http://scanme.nmap.org/index.html (1234 bytes)
  [200] http://scanme.nmap.org/about.html (567 bytes)
  [403] http://scanme.nmap.org/admin (0 bytes)

📝 SUMMARY & RECOMMENDATIONS
----------------------------------------------------------------------
Risk Level: LOW
Technologies: 5
Directories: 3

Recommendations:
  • Consider implementing a Web Application Firewall (WAF)
  • Update outdated software: Apache/2.4.7
```

---

## 🔧 Installation der Tools

```bash
# Auf Kali Linux (empfohlen)
sudo apt-get install -y ffuf gobuster whatweb wafw00f

# ProjectDiscovery Tools
cd ~/tools
# subfinder
wget https://github.com/projectdiscovery/subfinder/releases/latest/download/subfinder_2.6.6_linux_amd64.zip
unzip subfinder_*.zip && sudo mv subfinder /usr/local/bin/

# httpx
wget https://github.com/projectdiscovery/httpx/releases/latest/download/httpx_1.6.10_linux_amd64.zip
unzip httpx_*.zip && sudo mv httpx /usr/local/bin/
```

---

## 📝 Roadmap

### Geplante Integrationen

- [ ] **Subfinder** - Subdomain Discovery
- [ ] **HTTPX** - Fast HTTP Prober
- [ ] **Naabu** - Port Scanner
- [ ] **Gobuster** - Alternative Directory Bruteforce
- [ ] **Nikto** - Web Vulnerability Scanner

### Verbesserungen

- [ ] Mehr Wortlisten unterstützen
- [ ] Parallelisierung verbessern
- [ ] Cache für wiederholte Scans
- [ ] SIEM Integration für neue Tools

---

## 🤝 Contributing

Neue Tools hinzufügen:

1. Erstelle `tools/<tool>_integration.py`
2. Implementiere Async/Sync Wrapper
3. Füge Tests hinzu
4. Dokumentiere in diesem Guide

---

*Generated for Zen-AI-Pentest Framework v2.3.9*
