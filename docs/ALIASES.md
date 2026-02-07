# Zen-AI Pentest Aliase

Schnellzugriff auf alle wichtigen Tools via Kurzbefehle.

## PowerShell (Empfohlen)

### Installation

```powershell
# Aliase wurden automatisch zu deinem Profil hinzugefuegt
# Neues PowerShell-Fenster oeffnen oder Profil neu laden:
. $PROFILE
```

### Verfuegbare Aliase

| Alias | Befehl | Beschreibung |
|-------|--------|--------------|
| `zki` | `python tools/kimi_helper.py` | Kimi Helper (allgemein) |
| `zrecon` | `python tools/kimi_helper.py -p recon` | Recon Persona |
| `zexploit` | `python tools/kimi_helper.py -p exploit` | Exploit Persona |
| `zreport` | `python tools/kimi_helper.py -p report` | Report Persona |
| `zaudit` | `python tools/kimi_helper.py -p audit` | Audit Persona |
| `zsetup` | `python scripts/setup_wizard.py` | Setup Wizard |
| `zcheck` | `python scripts/check_config.py` | Config Check |
| `zswitch` | `python scripts/switch_model.py` | Model Switcher |

### Beispiele

```powershell
# Recon-Analyse
zrecon "Finde Subdomains von example.com"

# Exploit entwickeln
zexploit "Schreibe SQLi-Scanner fuer login.php"

# Bericht erstellen
zreport "CVSS-Bericht fuer XSS auf admin.php"

# Code review
zaudit "Review diese Funktion auf SQL Injection"

# Konfiguration pruefen
zcheck

# Backend wechseln
zswitch -b openai -m gpt-4o

# Interaktiver Modus
zki -i
```

## CMD (Eingabeaufforderung)

### Verwendung

```cmd
# Hilfe anzeigen
scripts\zen-alias.bat help

# Recon
scripts\zen-alias.bat zrecon "Scan target.com"

# Exploit
scripts\zen-alias.bat zexploit "Buffer Overflow PoC"

# Config check
scripts\zen-alias.bat zcheck
```

## Bash (WSL/Git Bash)

```bash
# Fuege zu ~/.bashrc hinzu:
alias zki='python3 ~/zen-ai-pentest/tools/kimi_helper.py'
alias zrecon='python3 ~/zen-ai-pentest/tools/kimi_helper.py -p recon'
alias zexploit='python3 ~/zen-ai-pentest/tools/kimi_helper.py -p exploit'
alias zreport='python3 ~/zen-ai-pentest/tools/kimi_helper.py -p report'
alias zaudit='python3 ~/zen-ai-pentest/tools/kimi_helper.py -p audit'
alias zsetup='python3 ~/zen-ai-pentest/scripts/setup_wizard.py'
alias zcheck='python3 ~/zen-ai-pentest/scripts/check_config.py'
alias zswitch='python3 ~/zen-ai-pentest/scripts/switch_model.py'

# Dann laden:
source ~/.bashrc
```

## Zsh (macOS/Linux)

```zsh
# Fuege zu ~/.zshrc hinzu:
alias zki='python3 ~/zen-ai-pentest/tools/kimi_helper.py'
alias zrecon='python3 ~/zen-ai-pentest/tools/kimi_helper.py -p recon'
alias zexploit='python3 ~/zen-ai-pentest/tools/kimi_helper.py -p exploit'
alias zreport='python3 ~/zen-ai-pentest/tools/kimi_helper.py -p report'
alias zaudit='python3 ~/zen-ai-pentest/tools/kimi_helper.py -p audit'
alias zsetup='python3 ~/zen-ai-pentest/scripts/setup_wizard.py'
alias zcheck='python3 ~/zen-ai-pentest/scripts/check_config.py'
alias zswitch='python3 ~/zen-ai-pentest/scripts/switch_model.py'

# Dann laden:
source ~/.zshrc
```

## Tastenkombinationen (PowerShell)

```powershell
# Optional: Tastenkuerzel hinzufuegen
Set-PSReadLineKeyHandler -Chord Ctrl+Shift+R -ScriptBlock {
    [Microsoft.PowerShell.PSConsoleReadLine]::RevertLine()
    [Microsoft.PowerShell.PSConsoleReadLine]::Insert('zrecon ""')
    [Microsoft.PowerShell.PSConsoleReadLine]::SetCursorPosition(9)
}

Set-PSReadLineKeyHandler -Chord Ctrl+Shift+E -ScriptBlock {
    [Microsoft.PowerShell.PSConsoleReadLine]::RevertLine()
    [Microsoft.PowerShell.PSConsoleReadLine]::Insert('zexploit ""')
    [Microsoft.PowerShell.PSConsoleReadLine]::SetCursorPosition(11)
}
```

## Typischer Workflow

```powershell
# 1. Konfiguration pruefen
zcheck

# 2. Setup (falls noetig)
zsetup -b kimi -m kimi-k2.5 -k "sk-..."

# 3. Recon durchfuehren
zrecon "Analysiere target.com"

# 4. Exploit entwickeln
zexploit "Schreibe PoC fuer gefundene Luecke"

# 5. Bericht erstellen
zreport "CVSS-Bericht mit Remediation"
```

## Fehlersuche

### "Der Befehl zki wurde nicht gefunden"

```powershell
# PowerShell-Profil neu laden
. $PROFILE

# Oder neues PowerShell-Fenster oeffnen
```

### "Python wurde nicht gefunden"

```powershell
# Python zum PATH hinzufuegen
# Oder vollen Pfad verwenden:
C:\Python313\python.exe tools\kimi_helper.py ...
```
