# Frequently Asked Questions (FAQ)

## Allgemein

### Was ist Zen-AI-Pentest?

Zen-AI-Pentest ist ein autonomes, KI-gestütztes Penetration Testing Framework. Es kombiniert Large Language Models (LLMs) mit professionellen Security-Tools für automatisierte Sicherheitsanalysen.

### Ist es kostenlos?

Ja, Zen-AI-Pentest ist Open Source unter der MIT License. Einige KI-Backends (OpenAI, Anthropic) benötigen jedoch API-Keys mit Kosten.

### Welche KI-Modelle werden unterstützt?

- **Kimi AI** (empfohlen, kostengünstig)
- OpenAI GPT-4
- Anthropic Claude
- Google Gemini
- OpenRouter (Multi-Provider)

## Installation & Setup

### Welche Systemvoraussetzungen gibt es?

**Minimum:**
- Python 3.11+
- 4 GB RAM
- 10 GB Speicher

**Empfohlen:**
- Python 3.12
- 8 GB RAM
- 50 GB Speicher
- Docker

### Installation schlägt fehl - was tun?

```bash
# 1. Virtuelle Umgebung prüfen
source .venv/bin/activate
which python

# 2. Dependencies neu installieren
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall

# 3. Cache löschen
rm -rf ~/.cache/pip
```

## Konfiguration

### Vault oder .env - was ist besser?

| | Vault | .env |
|---|-------|------|
| **Sicherheit** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Einfachheit** | Mittel | Hoch |
| **Empfohlen für** | Production | Development |

**Für Anfänger:** Starte mit .env, migriere später zu Vault.

### Wie rotiere ich geleakte Secrets?

1. **Sofort:** Token in GitHub/GitLab revoke
2. **Neuen Token generieren**
3. **In Secrets aktualisieren**
4. **History bereinigen (falls nötig):**
   ```bash
   git filter-branch --force --index-filter \
   "git rm --cached --ignore-unmatch .env" \
   --prune-empty --tag-name-filter cat -- --all
   ```

## Nutzung

### Ist das legal?

**Nur auf Systemen, die dir gehören oder für die du explizite Erlaubnis hast!**

- ✅ Deine eigenen Server
- ✅ Bug Bounty Programme
- ✅ Penetration Testing Verträge
- ❌ Fremde Systeme ohne Erlaubnis

### Wie starte ich einen Scan?

**Via CLI:**
```bash
python3 -m agents.cli recon --target example.com
```

**Via API:**
```bash
curl -X POST http://localhost:8000/api/v1/scans \
  -H "Authorization: Bearer <token>" \
  -d '{"target": "example.com", "scan_type": "recon"}'
```

**Via Web UI:**
https://zen-ai-pentest.pages.dev

### Wie lange dauert ein Scan?

| Scan-Typ | Dauer |
|----------|-------|
| Recon (basic) | 2-5 Minuten |
| Full Scan | 15-30 Minuten |
| Mit Exploitation | 30-60 Minuten |

## Fehlerbehebung

### "Authentication failed" bei Git push

1. GitHub App Auth prüfen:
   ```bash
   git config --local credential.helper
   ```

2. Neu einrichten:
   ```bash
   ~/zen-ai-pentest/setup-github-app-auth.sh .
   ```

### Pre-commit Hooks blockieren commits

```bash
# Auto-fix versuchen
pre-commit run --all-files

# Oder skip (nur in Notfällen!)
git commit -m "hotfix" --no-verify
```

### Datenbank-Verbindung fehlgeschlagen

```bash
# PostgreSQL läuft?
sudo systemctl status postgresql

# Datenbank existiert?
sudo -u postgres psql -l | grep zen_pentest

# Falls nicht:
sudo -u postgres createdb zen_pentest
```

## Sicherheit

### Werden meine Daten gespeichert?

- **Scan-Ergebnisse:** Lokal in PostgreSQL
- **Secrets:** In Vault oder .env (lokal)
- **Keine** Daten werden an externe Server gesendet (außer KI-APIs für Analyse)

### Ist Docker sicher?

Ja! Alle Tools laufen in:
- Isolierten Containern
- Read-only Dateisystemen
- Mit Resource Limits
- Network Isolation

### Was ist mit False Positives?

Die Risk Engine verwendet:
- Bayesian Filtering
- Multi-Faktor Validierung
- LLM Voting
- Manuelle Bestätigung bei High Risk

## Mitwirken

### Wie kann ich helfen?

1. **Code:** Pull Requests willkommen!
2. **Dokumentation:** Wiki verbessern
3. **Bug Reports:** Issues erstellen
4. **Feedback:** Discord beitreten

### Wo finde ich Hilfe?

- 📖 **Dokumentation:** Dieses Wiki
- 💬 **Discord:** https://discord.gg/BSmCqjhY
- 🐛 **Issues:** https://github.com/SHAdd0WTAka/zen-ai-pentest/issues
- 📧 **Email:** shadd0wtaka@protonmail.com

## Roadmap

### Q1 2026
- [ ] Mobile App
- [ ] Cloud Multi-Region Support
- [ ] Advanced Reporting

### Q2 2026
- [ ] ICS/SCADA Module
- [ ] Threat Intelligence Integration
- [ ] Auto-Remediation

### Q3 2026
- [ ] AI Model Fine-tuning
- [ ] Custom Agent Builder
- [ ] Enterprise SSO
