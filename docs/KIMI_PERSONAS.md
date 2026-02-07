# Kimi Personas für Zen-AI Pentest

Zen-AI Pentest bietet spezialisierte AI-Personas für verschiedene Pentesting-Phasen.

## Schnellstart

```bash
# Status prüfen
python tools/kimi_helper.py --check

# Mit Persona arbeiten
python tools/kimi_helper.py -p recon "Analysiere target.com"
python tools/kimi_helper.py -p exploit "SQLi-Scanner schreiben"
python tools/kimi_helper.py -p report "CVSS-Bericht erstellen"

# Interaktiver Modus
python tools/kimi_helper.py -i

# Oder mit lokaler kimi CLI
python tools/kimi_helper.py --cli -p recon
```

## Personas

| Persona | Emoji | Fokus |
|---------|-------|-------|
| **recon** | 🔍 | OSINT, Subdomains, Ports, Technologien |
| **exploit** | 💣 | Python-Exploits, POCs, Automation |
| **report** | 📝 | CVSS-Scoring, Remediation, Executive Summary |
| **audit** | 🔐 | Code Review, Security Audit, Bug Bounty |
| **network** | 🌐 | Infrastruktur, AD, Lateral Movement |
| **redteam** | 🕵️ | Adversary Simulation, APT TTPs |

## Zwei Modi

### API Mode (Standard)
Nutzt die Kimi API direkt - erfordert API Key.

```bash
python tools/kimi_helper.py -p recon "Scan target.com"
```

**Vorteile:**
- Keine lokale Installation nötig
- Funktioniert überall
- Bessere Fehlerbehandlung

### CLI Mode
Nutzt die lokale `kimi` CLI - erfordert Installation + Login.

```bash
# Einmalig installieren
pip install kimi-cli
kimi login

# Dann nutzen
python tools/kimi_helper.py --cli -p recon
```

**Vorteile:**
- Session-basierte Authentifizierung
- Interaktiver Chat
- Kein API Key Management

## Installation & Setup

### 1. API Mode Setup

```bash
# API Key konfigurieren
python scripts/setup_wizard.py -b kimi -m kimi-k2.5 -k "sk-your-key"

# Oder interaktiv
python scripts/setup_wizard.py
```

### 2. CLI Mode Setup

```bash
# kim CLI installieren
pip install kimi-cli

# Einloggen
kimi login
# oder
python tools/kimi_helper.py --login
```

### 3. Verifizieren

```bash
python tools/kimi_helper.py --check
```

## Aliase einrichten

### PowerShell

```powershell
# Automatisch (Windows)
.\scripts\setup_kimi_aliases.ps1

# Oder manuell in $PROFILE:
function zki { python "$env:USERPROFILE\zen-ai-pentest\tools\kimi_helper.py" @args }
function zrecon { python "$env:USERPROFILE\zen-ai-pentest\tools\kimi_helper.py" -p recon @args }
function zexploit { python "$env:USERPROFILE\zen-ai-pentest\tools\kimi_helper.py" -p exploit @args }
function zreport { python "$env:USERPROFILE\zen-ai-pentest\tools\kimi_helper.py" -p report @args }
function zaudit { python "$env:USERPROFILE\zen-ai-pentest\tools\kimi_helper.py" -p audit @args }
```

### Bash/Linux

```bash
# Automatisch
bash tools/setup_kimi_aliases.sh

# Oder manuell in ~/.bashrc:
alias zki='python3 ~/zen-ai-pentest/tools/kimi_helper.py'
alias zrecon='python3 ~/zen-ai-pentest/tools/kimi_helper.py -p recon'
alias zexploit='python3 ~/zen-ai-pentest/tools/kimi_helper.py -p exploit'
alias zreport='python3 ~/zen-ai-pentest/tools/kimi_helper.py -p report'
alias zaudit='python3 ~/zen-ai-pentest/tools/kimi_helper.py -p audit'
```

## Interaktiver Modus

```bash
python tools/kimi_helper.py -i
```

Befehle:
- `/recon`, `/exploit`, `/report`, `/audit`, `/network`, `/red` - Persona wechseln
- `/clear` - History löschen
- `/exit` - Beenden

## Beispiele

### Reconnaissance

```bash
zrecon "Finde alle Subdomains von example.com mit amass und subfinder"
zrecon "Nmap Scan für Top 1000 Ports auf 192.168.1.0/24"
zrecon "Technologie-Stack von target.com identifizieren"
```

### Exploit Development

```bash
zexploit "Python-Scanner für SQL Injection in Login-Formularen"
zexploit "PoC für CVE-2024-1234 als Python-Script"
zexploit "Buffer Overflow Exploit für vulnerable_app.exe"
```

### Reporting

```bash
zreport "CVSS-Bericht für XSS auf admin.php mit PoC"
zreport "Executive Summary für Critical SQL Injection"
zreport "Remediation Plan für 5 gefundene Schwachstellen"
```

### Code Audit

```bash
zaudit "Review login() Funktion auf Auth-Bypass"
zaudit "Suche nach Race Conditions in file_upload.py"
zaudit "OWASP Top 10 Analyse für api/endpoints.py"
```

## Troubleshooting

### "API Key nicht gefunden"

```bash
# Setup durchführen
python scripts/setup_wizard.py -b kimi -k "sk-your-key"

# Oder Umgebungsvariable setzen
export KIMI_API_KEY="sk-your-key"  # Linux/Mac
$env:KIMI_API_KEY="sk-your-key"    # PowerShell
```

### "kimi CLI nicht installiert"

```bash
pip install kimi-cli
kimi login
```

### "requests nicht installiert"

```bash
pip install requests rich
```

## Weitere Tools

| Tool | Zweck |
|------|-------|
| `scripts/setup_wizard.py` | API Keys konfigurieren |
| `scripts/check_config.py` | Konfiguration prüfen |
| `scripts/switch_model.py` | Backend/Modell wechseln |
| `scripts/ask-kimi.sh/ps1/bat` | Wrapper-Scripts |

## Siehe auch

- [README_USER_SETUP.md](../README_USER_SETUP.md) - Detaillierte Setup-Anleitung
- [ALIASES.md](ALIASES.md) - Alias-Dokumentation
