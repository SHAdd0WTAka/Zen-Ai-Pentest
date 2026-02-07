# SECURITY ALERT: API Key Exposed

## Incident Report

**Datum:** 2026-02-07  
**Schweregrad:** 🟡 MITTEL (Key wurde revoked)  
**Status:** TEILWEISE GELÖST

## Betroffener Key

```
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
```

**Provider:** OpenRouter (https://openrouter.ai/)  
**Status:** 🔴 REVOKED / UNGÜLTIG

## Zusammenfassung

- Key wurde während der Entwicklung in `.env` geschrieben und committed
- Key wurde sofort bei OpenRouter revoked
- Git-History Bereinigung wurde versucht, aber **blockiert** durch Branch Protection

## Warum Force-Push nicht möglich ist

```
remote: error: GH006: Protected branch update failed for refs/heads/master.
remote: Cannot force-push to this branch
```

Die GitHub Branch Protection verhindert Force-Pushes auf `master`.

## Durchgeführte Maßnahmen

### 1. ✅ Key REVOKEN
Der Key wurde bei OpenRouter sofort deaktiviert und ist nun wertlos.

### 2. ✅ Lokale Bereinigung
```bash
# Key aus aktueller .env entfernt
# Key aus Git-History lokal entfernt (git-filter-repo)
```

### 3. ⚠️ Remote History
Die alten Commits mit dem Key sind noch in der Git-History sichtbar, aber der Key ist **ungültig**.

## Prävention für Zukunft

```bash
# Pre-Commit Hook installieren
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Prüfe auf API Keys vor dem Commit
if git diff --cached | grep -E "(sk-or-|sk-)[a-zA-Z0-9]{20,}"; then
    echo "ERROR: API Key gefunden! Commit abgebrochen."
    exit 1
fi
EOF
chmod +x .git/hooks/pre-commit
```

## Empfohlene Workflow-Änderung

```bash
# NIE Keys direkt in .env schreiben
# Stattdessen:
python scripts/setup_wizard.py

# Oder Umgebungsvariable nutzen:
export OPENROUTER_API_KEY="sk-..."
```

## Verifizierung

- [x] Key bei OpenRouter revoked
- [x] Key aus aktueller `.env` entfernt
- [x] Key lokal aus History entfernt
- [ ] Remote History bereinigt (BLOCKIERT durch Branch Protection)

## Auswirkungen

- **Risiko:** Niedrig (Key ist revoked)
- **Sichtbarkeit:** Key ist in alter History sichtbar
- **Nutzbarkeit:** Key ist für Angreifer WERTLOS

## Nächste Schritte

1. Team über den Vorfall informieren
2. Alle Mitglieder müssen neue Keys generieren
3. Pre-Commit Hooks für alle empfohlen
4. Branch Protection bleibt aktiv (gut so!)

## Referenzen

- OpenRouter Dashboard: https://openrouter.ai/keys
- GitHub Branch Protection: https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/settings/branches
