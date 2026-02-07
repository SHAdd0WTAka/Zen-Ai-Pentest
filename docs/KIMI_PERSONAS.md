# Kimi CLI Personas für Zen-AI Pentest

## Übersicht

Personas sind spezialisierte System-Prompts für verschiedene Pentesting-Phasen.

## Verfügbare Personas

| Persona | Datei | Verwendung |
|---------|-------|------------|
| **Recon** | `~/.config/kimi/personas/recon.md` | OSINT, Subdomain-Scanning, Port-Scanning |
| **Exploit** | `~/.config/kimi/personas/exploit.md` | Exploit-Entwicklung, Python-Code |
| **Report** | `~/.config/kimi/personas/report.md` | Pentest-Berichte, CVSS-Scoring |
| **Audit** | `~/.config/kimi/personas/audit.md` | Code Review, Security Audit |

## Installation

### 1. Personas erstellen

```bash
# Linux/macOS
mkdir -p ~/.config/kimi/personas

# Windows
mkdir %USERPROFILE%\.config\kimi\personas
```

### 2. Wrapper-Script verwenden

#### Linux/macOS
```bash
# Recon-Modus
./scripts/ask-kimi.sh recon "Analysiere example.com"

# Exploit-Modus
./scripts/ask-kimi.sh exploit "Schreibe SQLi-Scanner"

# Report-Modus
./scripts/ask-kimi.sh report "CVSS-Bericht für XSS"
```

#### Windows (PowerShell)
```powershell
# Recon-Modus
.\scripts\ask-kimi.ps1 recon "Analysiere example.com"

# Exploit-Modus
.\scripts\ask-kimi.ps1 exploit "Schreibe SQLi-Scanner"
```

#### Windows (CMD)
```cmd
scripts\ask-kimi.bat recon "Analysiere example.com"
```

## Kimi Helper Tool (Empfohlen)

### Installation & Nutzung

```bash
# Liste alle Personas
python tools/kimi_helper.py --list

# One-Shot Anfrage
python tools/kimi_helper.py -p recon "Analysiere example.com"
python tools/kimi_helper.py -p exploit "SQLi-Scanner fuer login.php"
python tools/kimi_helper.py -p report "CVSS-Bericht fuer XSS"
python tools/kimi_helper.py -p audit "Review diese Python-Funktion"

# Aus Datei lesen
python tools/kimi_helper.py -p exploit -f request.txt

# Mit Temperature (Kreativitaet)
python tools/kimi_helper.py -p recon -t 0.3 "Scan example.com"

# Interaktiver Modus
python tools/kimi_helper.py -i
```

### Interaktiver Modus

```
/recon     -> Wechsle zu Recon Persona
/exploit   -> Wechsle zu Exploit Persona
/report    -> Wechsle zu Report Persona
/audit     -> Wechsle zu Audit Persona
/clear     -> History loeschen
/exit      -> Beenden
```

## Aliase (Optional)

### Linux/macOS (~/.bashrc oder ~/.zshrc)
```bash
alias recon='~/zen-ai-pentest/scripts/ask-kimi.sh recon'
alias exploit='~/zen-ai-pentest/scripts/ask-kimi.sh exploit'
alias report='~/zen-ai-pentest/scripts/ask-kimi.sh report'
```

### Windows (PowerShell $PROFILE)
```powershell
function recon { & "$env:USERPROFILE\zen-ai-pentest\scripts\ask-kimi.ps1" recon @args }
function exploit { & "$env:USERPROFILE\zen-ai-pentest\scripts\ask-kimi.ps1" exploit @args }
function report { & "$env:USERPROFILE\zen-ai-pentest\scripts\ask-kimi.ps1" report @args }
```

## Empfohlene Kimi-Einstellungen

| Einstellung | Coding | Recon | Reports |
|-------------|--------|-------|---------|
| **Model** | kimi-k2.5 | kimi-k2.5 | kimi-k2.5 |
| **Temperature** | 0.3 | 0.7 | 0.5 |
| **Max Tokens** | 2048 | 4096 | 8192 |

## Eigene Personas erstellen

Erstelle eine neue `.md` Datei in `~/.config/kimi/personas/`:

```markdown
Du bist ein [Spezialist für X].
- Regel 1
- Regel 2
- Output: Format
```

## Umgebungsvariablen

| Variable | Beschreibung | Standard |
|----------|--------------|----------|
| `KIMI_PERSONA_DIR` | Pfad zu den Persona-Dateien | `~/.config/kimi/personas` |

## Troubleshooting

### "kimi-cli nicht gefunden"
```bash
pip install kimi-cli
```

### "Persona nicht gefunden"
Prüfe, ob die `.md` Datei existiert:
```bash
ls ~/.config/kimi/personas/
```
