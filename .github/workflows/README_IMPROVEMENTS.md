# Verbesserte GitHub Actions Workflows

## Übersicht

Dieser Ordner enthält verbesserte Versionen der GitHub Actions Workflows mit folgenden Verbesserungen:

### 🔧 Allgemeine Verbesserungen

1. **Concurrency** - Verhindert Race Conditions bei parallelen Workflow-Runs
2. **Permissions** - Minimale Rechte für maximale Sicherheit
3. **Timeout** - Verhindert hängende Jobs
4. **Debug Steps** - Einfacheres Debugging mit Umgebungs-Info
5. **Artefakt-Upload** - Logs werden bei Fehlern automatisch hochgeladen
6. **Caching** - Optimierte Cache-Konfiguration für schnellere Builds
7. **Action-Versionen** - Aktualisiert auf @v4/@v5

### 📁 Dateien

| Datei | Beschreibung |
|-------|-------------|
| `ci-improved.yml` | Verbesserter CI/CD Pipeline |
| `security-improved.yml` | Verbesserter Security Scan |
| `deploy-improved.yml` | Verbesserter Deploy Workflow |
| `health-check-fixed.yml` | Health Check mit gefixten Action-Versionen |
| `docker-fixed.yml` | Docker Build mit gefixten Action-Versionen |

### 🚀 Verwendung

1. **Backup** der bestehenden Workflows erstellen:
   ```bash
   mv ci.yml ci.yml.backup
   mv security.yml security.yml.backup
   mv deploy.yml deploy.yml.backup
   mv health-check.yml health-check.yml.backup
   mv docker.yml docker.yml.backup
   ```

2. **Neue Workflows aktivieren**:
   ```bash
   mv ci-improved.yml ci.yml
   mv security-improved.yml security.yml
   mv deploy-improved.yml deploy.yml
   mv health-check-fixed.yml health-check.yml
   mv docker-fixed.yml docker.yml
   ```

3. **Tests durchführen**:
   - Workflow manuell über Actions-Tab starten
   - Logs auf Fehler prüfen
   - Artefakte bei Fehlern überprüfen

### ✅ Checkliste für neue Workflows

- [ ] Concurrency gesetzt?
- [ ] Permissions minimal aber ausreichend?
- [ ] actions/checkout@v4 verwendet?
- [ ] setup-python@v5 mit Cache?
- [ ] setup-node@v4 mit Cache?
- [ ] timeout-minutes gesetzt?
- [ ] Debug-Steps vor kritischen Schritten?
- [ ] Artefakt-Upload bei Fehlern?
- [ ] fail-fast: false bei Matrix?

### 📝 Wichtige Hinweise

- **package-lock.json** muss committed sein für Node-Jobs
- **requirements.txt** muss committed sein für Python-Jobs
- Secrets müssen in Repository Settings gesetzt sein
- Environment Protection Rules für Deployments prüfen

### 🔍 Troubleshooting

| Problem | Lösung |
|---------|--------|
| Action nicht gefunden | Version prüfen (@v4 statt @v6) |
| npm ci fehlschlägt | package-lock.json committed? |
| pip install langsam | Cache korrekt konfiguriert? |
| Permission denied | permissions in Workflow prüfen |
| Race Conditions | concurrency hinzufügen |

### 📊 Vergleich: Alt vs. Neu

| Feature | Alt | Neu |
|---------|-----|-----|
| Concurrency | ❌ | ✅ |
| Permissions | ⚠️ Teilweise | ✅ Überall |
| Timeout | ❌ | ✅ |
| Debug Steps | ❌ | ✅ |
| Artefakt-Upload | ⚠️ Teilweise | ✅ Bei Fehlern |
| Action-Versionen | ⚠️ @v6 (falsch) | ✅ @v4/@v5 |

### 🔄 Rollback

Falls Probleme auftreten:
```bash
git checkout HEAD -- .github/workflows/
```
