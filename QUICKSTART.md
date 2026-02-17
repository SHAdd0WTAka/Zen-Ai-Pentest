# 🚀 Quick-Start Guide

> **In 5 Minuten zum ersten Scan**

---

## ⚡ 1-Minute Setup

```bash
# 1. Repository klonen
git clone https://github.com/SHAdd0WTAka/Zen-Ai-Pentest.git
cd Zen-Ai-Pentest

# 2. Tools installieren (nur auf Kali/Ubuntu)
sudo apt-get install -y nmap nikto ffuf whatweb wafw00f tshark sqlmap

# 3. Fertig! Teste es:
python -m modules.enhanced_recon --target scanme.nmap.org --mode tech
```

---

## 🎯 Häufige Befehle

### Schnelle Scans

```bash
# Technologie-Erkennung (10 Sekunden)
python -m modules.enhanced_recon -t example.com --mode tech

# WAF Detection (15 Sekunden)
python -m modules.enhanced_recon -t example.com --mode waf

# Directory Scan (1-2 Minuten)
python -m modules.enhanced_recon -t example.com --mode dir
```

### Komplette Scans

```bash
# Full Recon (2-5 Minuten)
python -m modules.enhanced_recon -t example.com --mode full

# Super Scanner (5-15 Minuten) - ALLES
python -m modules.super_scanner -t example.com
```

### OSINT

```bash
# Username auf 400+ Plattformen suchen
python -m modules.osint_super -u johndoe

# Email prüfen
python -m modules.osint_super -e user@example.com

# Domain investigieren
python -m modules.osint_super -d example.com
```

---

## 📋 Cheat Sheet

| Was willst du? | Befehl |
|----------------|--------|
| **Ports scannen** | `python -m modules.enhanced_recon -t target.com --mode full` |
| **Technologien** | `python -m modules.enhanced_recon -t target.com --mode tech` |
| **Subdomains** | `python -m modules.osint_super -d target.com` |
| **Directories** | `python -m modules.enhanced_recon -t target.com --mode dir` |
| **WAF erkennen** | `python -m modules.enhanced_recon -t target.com --mode waf` |
| **Alles auf einmal** | `python -m modules.super_scanner -t target.com` |
| **Username OSINT** | `python -m modules.osint_super -u username` |
| **Email OSINT** | `python -m modules.osint_super -e email@test.com` |

---

## 🐍 Python API (3 Zeilen)

```python
# Technologien erkennen
from tools.whatweb_integration import scan_sync
result = scan_sync("http://example.com")

# Subdomains finden
from tools.subfinder_integration import enumerate_sync
result = enumerate_sync("example.com")

# Directory fuzzing
from tools.ffuf_integration_enhanced import directory_bruteforce_sync
result = directory_bruteforce_sync("http://example.com/FUZZ")
```

---

## 🧪 Sichere Test-Ziele

```bash
# ✅ Diese kannst du ohne Genehmigung testen:
# - scanme.nmap.org
# - testphp.vulnweb.com
# - Dein eigener Rechner (127.0.0.1)
# - Deine eigenen VMs

# ❌ NIE ohne Genehmigung:
# - Produktiv-Systeme
# - Government/Banken
# - Andere Websites
```

---

## 🔧 Fehlerbehebung

**"Command not found"**
```bash
# Ins Projekt-Verzeichnis wechseln
cd /pfad/zu/Zen-Ai-Pentest

# Oder venv aktivieren
source venv/bin/activate
```

**"Permission denied" (Nmap)**
```bash
# Mit sudo ausführen
sudo python -m modules.super_scanner -t target.com
```

**Module nicht gefunden**
```bash
# Abhängigkeiten installieren
pip install -r requirements.txt
```

---

## 📚 Weitere Dokumentation

- [Vollständiges Tutorial](TUTORIAL.md) - Alles im Detail
- [Tools Übersicht](README_ENHANCED_TOOLS.md) - Alle 15 Tools
- [API Dokumentation](docs/API.md) - REST API

---

**🎉 Fertig! Jetzt kannst du loslegen!**
