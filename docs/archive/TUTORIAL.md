# 🎓 Zen-AI-Pentest Framework - Komplettes Tutorial

> **Lerne Schritt-für-Schritt, wie du das Zen-AI-Pentest Framework professionell nutzt**

---

## 📋 Inhaltsverzeichnis

1. [Installation & Setup](#1-installation--setup)
2. [Erste Schritte](#2-erste-schritte)
3. [Tool-Übersicht](#3-tool-übersicht)
4. [Grundlegende Scans](#4-grundlegende-scans)
5. [Erweiterte Scans](#5-erweiterte-scans)
6. [OSINT Investigation](#6-osint-investigation)
7. [Super Scanner](#7-super-scanner)
8. [API-Nutzung](#8-api-nutzung)
9. [Best Practices](#9-best-practices)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Installation & Setup

### 1.1 System-Voraussetzungen

```bash
# Unterstützte Betriebssysteme
- ✅ Kali Linux (empfohlen)
- ✅ Ubuntu 20.04+
- ✅ Debian 11+
- ✅ Windows 10/11 (WSL2)
- ✅ macOS (mit Homebrew)
```

### 1.2 Repository klonen

```bash
# Clone das Repository
git clone https://github.com/SHAdd0WTAka/Zen-Ai-Pentest.git
cd Zen-Ai-Pentest

# Oder aktualisiere bestehendes Repo
git pull origin main
```

### 1.3 Python-Abhängigkeiten installieren

```bash
# Virtuelle Umgebung erstellen (empfohlen)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Für Entwicklung
```

### 1.4 Externe Tools installieren

```bash
# Auf Kali Linux (einfachste Methode)
sudo apt-get update
sudo apt-get install -y \
    nmap \
    masscan \
    nikto \
    ffuf \
    gobuster \
    whatweb \
    wafw00f \
    tshark \
    sqlmap \
    amass \
    git

# ProjectDiscovery Tools (Subfinder, HTTPX, Nuclei)
cd ~/tools

# Subfinder
wget https://github.com/projectdiscovery/subfinder/releases/latest/download/subfinder_linux_amd64.zip
unzip subfinder_linux_amd64.zip
sudo mv subfinder /usr/local/bin/

# HTTPX
wget https://github.com/projectdiscovery/httpx/releases/latest/download/httpx_linux_amd64.zip
unzip httpx_linux_amd64.zip
sudo mv httpx /usr/local/bin/

# Nuclei
wget https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_linux_amd64.zip
unzip nuclei_linux_amd64.zip
sudo mv nuclei /usr/local/bin/
nuclei -update-templates

# Python-Tools (Sherlock, Ignorant)
pip install sherlock-project ignorant
```

### 1.5 Installation verifizieren

```bash
# Test-Script ausführen
python -c "
from tools.nmap_integration import NmapScanner
from tools.whatweb_integration import WhatWebIntegration
from modules.enhanced_recon import EnhancedReconModule
print('✅ Alle Module erfolgreich geladen!')
"

# Tools prüfen
which nmap nuclei sqlmap ffuf whatweb wafw00f subfinder httpx nikto tshark
```

---

## 2. Erste Schritte

### 2.1 CLI-Hilfe anzeigen

```bash
# Haupt-Script Hilfe
python zen_ai_pentest.py --help

# Enhanced Recon Hilfe
python -m modules.enhanced_recon --help

# OSINT Super Hilfe
python -m modules.osint_super --help

# Super Scanner Hilfe
python -m modules.super_scanner --help
```

### 2.2 Erster Test-Scan

```bash
# Scanne die offizielle Nmap-Test-Seite (sicher!)
python -m modules.enhanced_recon --target scanme.nmap.org --mode tech

# Du wirst gefragt:
# ⚠️  SAFETY CHECK
# Target: scanme.nmap.org
# Ensure you have authorization to scan this target!
# Continue? (yes/no):

# Tippe: yes
```

**Erwartete Ausgabe:**
```
📊 TECHNOLOGY DETECTION
----------------------------------------------------------------------
Found 5 technologies:
  • Apache [2.4.7] [100%]
  • Ubuntu Linux [100%]
  • Google-Analytics [Universal] [100%]
  • HTML5 [100%]
```

---

## 3. Tool-Übersicht

### 3.1 Nach Kategorie

| Kategorie | Tools | Zweck |
|-----------|-------|-------|
| **Port Scanning** | Nmap, Masscan | Offene Ports und Services finden |
| **Web Scanning** | Nuclei, Nikto, FFuF | Web-Schwachstellen finden |
| **Reconnaissance** | Subfinder, Amass | Subdomains aufdecken |
| **Technologie** | WhatWeb, HTTPX | Tech-Stack identifizieren |
| **OSINT** | Sherlock, Ignorant | Social Media & Email OSINT |
| **Netzwerk** | TShark, WAFW00F | Traffic-Analyse, WAF-Erkennung |

### 3.2 Nach Sicherheitsstufe

```
🟢 SAFE (Read-Only)
├── WhatWeb (Technologie-Erkennung)
├── Subfinder (Passive Enumeration)
├── HTTPX (HTTP Probing)
└── Sherlock (OSINT)

🟡 NORMAL (Standard-Scans)
├── Nmap (Port Scanning)
├── FFuF (Directory Fuzzing)
├── WAFW00F (WAF Detection)
└── Amass (Active Enumeration)

🟠 DANGEROUS (Kann Logs erzeugen)
├── Nikto (Vulnerability Scanning)
├── Masscan (High-Speed Scanning)
└── Nuclei (Active Probing)

🔴 CRITICAL (Exploitation)
└── SQLMap (SQL Injection Testing)
```

---

## 4. Grundlegende Scans

### 4.1 Einzelne Tools nutzen

#### Nmap - Port Scanning

```python
# In Python
from tools.nmap_integration import NmapScanner

# Scanner erstellen
scanner = NmapScanner(target="example.com")

# Top 1000 Ports scannen
result = scanner.scan_top_ports()

for port in result.ports:
    print(f"Port {port.port}: {port.service} {port.version}")
```

```bash
# Oder direkt via Command Line
nmap -F -sV example.com
```

#### WhatWeb - Technologie-Erkennung

```python
from tools.whatweb_integration import scan_sync

result = scan_sync("http://example.com")

for tech in result.technologies:
    print(f"{tech.name} {tech.version} [{tech.category}]")
```

**Beispiel-Ausgabe:**
```
Apache 2.4.41 [Web Server]
PHP 7.4.3 [Programming Language]
WordPress 5.8.1 [CMS]
jQuery 3.6.0 [JavaScript Library]
Bootstrap 4.5.2 [CSS Framework]
```

#### Subfinder - Subdomain Enumeration

```python
from tools.subfinder_integration import enumerate_sync

result = enumerate_sync("example.com")

print(f"Found {result.count} subdomains:")
for subdomain in result.subdomains[:10]:
    print(f"  • {subdomain}")
```

#### FFuF - Directory Bruteforce

```python
from tools.ffuf_integration_enhanced import directory_bruteforce_sync

result = directory_bruteforce_sync(
    "http://example.com/FUZZ",
    extensions=["php", "html", "txt", "js"],
    threads=20
)

for finding in result.findings:
    print(f"[{finding.status_code}] {finding.url}")
```

### 4.2 Kombinierte Scans

```bash
# Enhanced Recon - Alle Modi
python -m modules.enhanced_recon --target example.com --mode full

# Einzelne Modi
python -m modules.enhanced_recon --target example.com --mode tech    # Technologien
python -m modules.enhanced_recon --target example.com --mode waf     # WAF Detection
python -m modules.enhanced_recon --target example.com --mode dir     # Directories
```

---

## 5. Erweiterte Scans

### 5.1 Programmatische Nutzung

```python
import asyncio
from modules.enhanced_recon import EnhancedReconModule

async def run_recon():
    # Module initialisieren
    recon = EnhancedReconModule()

    # Vollständige Reconnaissance
    result = recon.full_recon("example.com")

    # Ergebnisse auswerten
    print(f"Risk Level: {result['summary']['risk_level']}")
    print(f"Technologien: {result['summary']['technologies_detected']}")
    print(f"Directories: {result['summary']['directories_found']}")

    # Empfehlungen anzeigen
    for rec in result['summary']['recommendations']:
        print(f"💡 {rec}")

# Ausführen
asyncio.run(run_recon())
```

### 5.2 Batch-Scanning mehrerer Ziele

```python
import asyncio
from modules.enhanced_recon import EnhancedReconModule

targets = ["example.com", "test.com", "demo.com"]

async def batch_scan():
    recon = EnhancedReconModule()

    results = []
    for target in targets:
        print(f"Scanning {target}...")
        result = await recon.run_full_scan(target)
        results.append(result)

    # Zusammenfassung
    print(f"\n{'='*60}")
    print("BATCH SCAN SUMMARY")
    print(f"{'='*60}")
    for result in results:
        print(f"{result.target}: {result.summary['risk_level']}")

asyncio.run(batch_scan())
```

### 5.3 Custom Wordlists

```python
from tools.ffuf_integration_enhanced import FFuFIntegration

ffuf = FFuFIntegration(wordlist_dir="/path/to/custom/wordlists")

# Mit eigener Wordlist
result = await ffuf.directory_bruteforce(
    "http://example.com/FUZZ",
    wordlist="/path/to/custom/directories.txt",
    extensions=["php", "jsp", "aspx"]
)
```

---

## 6. OSINT Investigation

### 6.1 Username Investigation

```bash
# Suche nach Username auf 400+ Plattformen
python -m modules.osint_super --username johndoe

# Ausgabe:
# 👤 Social Media Accounts: 15
#   ✓ twitter: https://twitter.com/johndoe
#   ✓ github: https://github.com/johndoe
#   ✓ instagram: https://instagram.com/johndoe
```

**Python API:**
```python
from tools.sherlock_integration import search_sync

result = search_sync("johndoe")

for account in result.found_sites:
    print(f"Found on {account['site']}: {account['url']}")
```

### 6.2 Email Investigation

```bash
# Überprüfe Email auf 120+ Plattformen
python -m modules.osint_super --email user@example.com
```

**Python API:**
```python
from tools.ignorant_integration import check_email_sync

result = check_email_sync("user@example.com")

print(f"Email found on {len(result.found_platforms)} platforms:")
for platform in result.found_platforms:
    print(f"  • {platform.platform}: {platform.url}")
```

### 6.3 Domain Investigation

```bash
# Komplette Domain-Investigation
python -m modules.osint_super --domain example.com

# Ergebnisse:
# - Subdomains (Subfinder + Amass)
# - Technologien (WhatWeb)
# - Risk Assessment
```

---

## 7. Super Scanner

### 7.1 Der Super Scanner ist die Komplettlösung

```bash
# Ein Befehl, 7 Phasen, alle Tools
python -m modules.super_scanner --target example.com

# Phasen:
# [1/7] 🔍 Subdomain Enumeration
# [2/7] 🌐 HTTP Probing
# [3/7] 🔧 Technology Detection
# [4/7] 🛡️  WAF Detection
# [5/7] 📡 Port Scanning
# [6/7] 📁 Directory Bruteforce
# [7/7] 🐛 Vulnerability Scanning
```

### 7.2 Ergebnisse interpretieren

```bash
# Der Super Scanner generiert:
# - JSON Report mit allen Ergebnissen
# - Risk Level (LOW/MEDIUM/HIGH/CRITICAL)
# - Konkrete Empfehlungen
# - Statistiken
```

**Beispiel-Output:**
```
📊 SUPER SCAN REPORT
======================================================================
Target: example.com
🎯 RISK LEVEL: MEDIUM
📈 Risk Score: 45/100

📋 STATISTICS
----------------------------------------------------------------------
  Subdomains: 23
  Live Hosts: 8
  Technologies: 5
  Open Ports: 4
  Directories: 12
  Vulnerabilities: 3

💡 RECOMMENDATIONS
----------------------------------------------------------------------
  • Implement a Web Application Firewall (WAF)
  • Close unnecessary ports and services
  • Restrict access to sensitive directories
  • Address identified vulnerabilities immediately
```

---

## 8. API-Nutzung

### 8.1 Server starten

```bash
# API Server starten
cd api
python main.py

# Oder mit uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 8.2 API Endpunkte

```bash
# Swagger UI öffnen
http://localhost:8000/docs

# Scan starten
curl -X POST "http://localhost:8000/api/v1/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "example.com",
    "scan_type": "full",
    "tools": ["nmap", "whatweb", "subfinder"]
  }'

# Ergebnisse abrufen
curl "http://localhost:8000/api/v1/scan/{scan_id}/results"
```

---

## 9. Best Practices

### 9.1 Sicherheit

```bash
# ✅ IMMER vor dem Scan:
# 1. Genehmigung einholen!
# 2. Scope definieren!
# 3. Notfall-Kontakt festlegen!

# ✅ Sichere Targets zum Testen:
# - scanme.nmap.org (Nmap Test-Server)
# - testphp.vulnweb.com (Acunetix Test-Site)
# - Deine eigenen VMs/Labs

# ❌ NIE ohne Genehmigung:
# - Produktiv-Systeme
# - Government-Sites
# - Banken/Finanzdienste
```

### 9.2 Performance-Optimierung

```python
# Für große Netzwerke
from tools.masscan_integration import MasscanIntegration

# Masscan ist 100x schneller als Nmap
masscan = MasscanIntegration(rate=100000)  # 100k PPS
result = await masscan.scan("192.168.1.0/24", ports="1-65535")

# Für viele Subdomains
from tools.httpx_integration import HTTPXIntegration

httpx = HTTPXIntegration(threads=100)  # 100 parallele Requests
result = await httpx.probe(subdomains_list)
```

### 9.3 Stealth-Modus

```python
# Langsamer, aber unauffälliger
from tools.nmap_integration import NmapScanner
from tools.ffuf_integration_enhanced import FFuFIntegration

# Nmap mit Timing T2 (sneaky)
nmap = NmapScanner(target="example.com", timing="T2")

# FFuF mit weniger Threads
ffuf = FFuFIntegration()
result = await ffuf.directory_bruteforce(
    target="http://example.com/FUZZ",
    threads=10,  # Weniger Threads
    extensions=["html"]  # Weniger Extensions
)
```

---

## 10. Troubleshooting

### 10.1 Häufige Fehler

**Fehler: Tool nicht gefunden**
```bash
# Lösung: Prüfe PATH
which nmap nuclei sqlmap

# Falls nicht gefunden:
export PATH=$PATH:/usr/local/bin
```

**Fehler: Permission denied (Nmap/Masscan)**
```bash
# Lösung: Mit sudo oder CAP_NET_RAW
sudo nmap -sS target.com

# Oder CAP_NET_RAW setzen:
sudo setcap cap_net_raw+cap_net_admin+eip /usr/bin/nmap
```

**Fehler: Module not found**
```bash
# Lösung: Im Projekt-Verzeichnis ausführen
cd /pfad/zu/Zen-Ai-Pentest
python -m modules.enhanced_recon --target example.com
```

### 10.2 Debug-Modus

```python
import logging

# Debug-Logging aktivieren
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Jetzt werden alle Details geloggt
```

### 10.3 Support

```
Bei Problemen:
1. README_ENHANCED_TOOLS.md lesen
2. Tests ausführen: pytest tests/ -v
3. GitHub Issues: https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/issues
4. Discord Community: https://discord.gg/BSmCqjhY
```

---

## 🎯 Zusammenfassung

Du hast gelernt:
- ✅ Installation aller Tools
- ✅ Grundlegende & erweiterte Scans
- ✅ OSINT Investigation
- ✅ Super Scanner Nutzung
- ✅ API Integration
- ✅ Best Practices

### Schnell-Referenz

```bash
# Einzelne Scans
python -m modules.enhanced_recon --target example.com --mode tech

# OSINT
python -m modules.osint_super --username johndoe

# Alles zusammen
python -m modules.super_scanner --target example.com
```

### Nächste Schritte

1. **Teste** mit scanme.nmap.org
2. **Experimentiere** mit verschiedenen Tools
3. **Lese** die erweiterte Dokumentation
4. **Baue** eigene Workflows

---

**🎉 Viel Erfolg beim Pentesting - immer ethisch und legal!**

*Letzte Aktualisierung: 2026-02-17*
*Version: 2.3.9+*
