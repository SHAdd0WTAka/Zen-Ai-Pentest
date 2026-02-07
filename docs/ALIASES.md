# Zen-AI Pentest Aliase

Schnellzugriff auf alle wichtigen Tools via Kurzbefehle.

## Automatische Installation

### PowerShell (Windows)

```powershell
# Aliase werden automatisch beim ersten Setup hinzugefügt
# Profil neu laden oder neues PowerShell-Fenster öffnen:
. $PROFILE
```

### Bash (Linux/macOS/WSL)

```bash
# Füge zu ~/.bashrc hinzu:
echo 'alias zki="python3 ~/zen-ai-pentest/tools/kimi_helper.py"' >> ~/.bashrc
echo 'alias zrecon="python3 ~/zen-ai-pentest/tools/kimi_helper.py -p recon"' >> ~/.bashrc
echo 'alias zexploit="python3 ~/zen-ai-pentest/tools/kimi_helper.py -p exploit"' >> ~/.bashrc
echo 'alias zreport="python3 ~/zen-ai-pentest/tools/kimi_helper.py -p report"' >> ~/.bashrc
echo 'alias zaudit="python3 ~/zen-ai-pentest/tools/kimi_helper.py -p audit"' >> ~/.bashrc

# Laden
source ~/.bashrc
```

## Verfügbare Aliase

| Alias | Befehl | Beschreibung |
|-------|--------|--------------|
| `zki` | `python tools/kimi_helper.py` | Kimi Helper (allgemein) |
| `zrecon` | `python tools/kimi_helper.py -p recon` | 🔍 Recon Persona |
| `zexploit` | `python tools/kimi_helper.py -p exploit` | 💣 Exploit Persona |
| `zreport` | `python tools/kimi_helper.py -p report` | 📝 Report Persona |
| `zaudit` | `python tools/kimi_helper.py -p audit` | 🔐 Audit Persona |
| `zsetup` | `python scripts/setup_wizard.py` | Setup Wizard |
| `zcheck` | `python scripts/check_config.py` | Config Check |
| `zswitch` | `python scripts/switch_model.py` | Model Switcher |

## Manuelle Einrichtung

### PowerShell ($PROFILE)

```powershell
# Zeige Profil-Pfad
$PROFILE

# Bearbeiten
notepad $PROFILE
```

Füge hinzu:

```powershell
# Zen-AI Pentest Aliase
function zki { python "$env:USERPROFILE\zen-ai-pentest\tools\kimi_helper.py" @args }
function zrecon { python "$env:USERPROFILE\zen-ai-pentest\tools\kimi_helper.py" -p recon @args }
function zexploit { python "$env:USERPROFILE\zen-ai-pentest\tools\kimi_helper.py" -p exploit @args }
function zreport { python "$env:USERPROFILE\zen-ai-pentest\tools\kimi_helper.py" -p report @args }
function zaudit { python "$env:USERPROFILE\zen-ai-pentest\tools\kimi_helper.py" -p audit @args }
function zsetup { python "$env:USERPROFILE\zen-ai-pentest\scripts\setup_wizard.py" @args }
function zcheck { python "$env:USERPROFILE\zen-ai-pentest\scripts\check_config.py" }
function zswitch { python "$env:USERPROFILE\zen-ai-pentest\scripts\switch_model.py" @args }
```

### Zsh (~/.zshrc)

```zsh
# Zen-AI Pentest Aliase
alias zki='python3 ~/zen-ai-pentest/tools/kimi_helper.py'
alias zrecon='python3 ~/zen-ai-pentest/tools/kimi_helper.py -p recon'
alias zexploit='python3 ~/zen-ai-pentest/tools/kimi_helper.py -p exploit'
alias zreport='python3 ~/zen-ai-pentest/tools/kimi_helper.py -p report'
alias zaudit='python3 ~/zen-ai-pentest/tools/kimi_helper.py -p audit'
alias zsetup='python3 ~/zen-ai-pentest/scripts/setup_wizard.py'
alias zcheck='python3 ~/zen-ai-pentest/scripts/check_config.py'
alias zswitch='python3 ~/zen-ai-pentest/scripts/switch_model.py'
```

## CMD (Windows)

```cmd
# Verwende Batch-Wrapper
scripts\zen-alias.bat zrecon "Scan target.com"
scripts\zen-alias.bat zcheck
```

## Typischer Workflow

```bash
# 1. Konfiguration prüfen
zcheck

# 2. Setup (falls nötig)
zsetup -b kimi -m kimi-k2.5 -k "sk-..."

# 3. Recon durchführen
zrecon "Analysiere target.com"

# 4. Exploit entwickeln
zexploit "Schreibe PoC für gefundene Lücke"

# 5. Bericht erstellen
zreport "CVSS-Bericht mit Remediation"

# 6. Code review
zaudit "Reviewe die Implementierung"
```

## Interaktiver Modus

```bash
# Starten
zki -i

# Befehle:
/recon     → Wechsle zu Recon Persona
/exploit   → Wechsle zu Exploit Persona
/report    → Wechsle zu Report Persona
/audit     → Wechsle zu Audit Persona
/network   → Wechsle zu Network Persona
/red       → Wechsle zu RedTeam Persona
/clear     → History löschen
/exit      → Beenden
```

## CLI vs API Mode

```bash
# API Mode (Standard, erfordert Key)
zrecon "Scan target.com"

# CLI Mode (erfordert kim CLI)
zki --cli -p recon
```

## Troubleshooting

### "Der Befehl zki wurde nicht gefunden"

```powershell
# PowerShell-Profil neu laden
. $PROFILE

# Oder neues PowerShell-Fenster öffnen
```

### "Python wurde nicht gefunden"

```powershell
# Python zum PATH hinzufügen
# Oder vollen Pfad verwenden:
C:\Python313\python.exe tools\kimi_helper.py ...
```

### "Module nicht gefunden"

```bash
pip install -r requirements.txt
```

## Siehe auch

- [KIMI_PERSONAS.md](KIMI_PERSONAS.md) - Persona-Dokumentation
- [README_USER_SETUP.md](../README_USER_SETUP.md) - Setup-Anleitung
