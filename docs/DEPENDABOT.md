# Dependabot Configuration

Automatisierte Dependency Updates für Zen AI Pentest.

## 🚀 Aktivierung

Dependabot ist bereits konfiguriert! Es muss nur in den GitHub Repository Einstellungen aktiviert werden:

### Schritt 1: GitHub Einstellungen

1. Gehe zu: `https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/settings/security_analysis`
2. Unter "Dependabot" folgendes aktivieren:
   - ☑️ **Dependabot alerts** - Für Security Vulnerabilities
   - ☑️ **Dependabot security updates** - Automatische Security PRs
   - ☑️ **Dependabot version updates** - Regelmäßige Version Updates

### Schritt 2: Secrets (Optional)

Für private Registrys oder private Dependencies:

1. Gehe zu: `https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/settings/secrets/actions`
2. Füge hinzu:
   - `PYPI_API_TOKEN` - Für private PyPI packages
   - `NPM_TOKEN` - Für private NPM packages

## 📦 Konfigurierte Package Ecosystems

| Ecosystem | Verzeichnis | Frequenz | PR Limit |
|-----------|-------------|----------|----------|
| **pip** (Python) | `/` | Weekly | 10 |
| **npm** (Node.js) | `/postman` | Weekly | 5 |
| **docker** | `/` | Weekly | 5 |
| **docker** (Shield) | `/zen_shield` | Weekly | 3 |
| **github-actions** | `/.github/workflows` | Weekly | 10 |
| **pip** (Integration) | `/integration` | Weekly | 5 |
| **pip** (Docs) | `/docs` | Monthly | 3 |

## 🏷️ Labels

Dependabot PRs werden automatisch mit Labels versehen:

- `dependencies` - Alle Dependency Updates
- `python` / `javascript` / `docker` / `github-actions` - Nach Typ
- `postman` / `zen-shield` / `integration` / `documentation` - Nach Modul
- `security` - Für Security Updates

## 🔄 Update Verhalten

### Automatisches Merging

Kleine Updates werden automatisch gemerged:

| Update Type | Auto-Approve | Auto-Merge |
|-------------|--------------|------------|
| **Patch** (1.0.0 → 1.0.1) | ✅ Ja | ✅ Ja |
| **Minor** Dev Dependencies | ✅ Ja | ❌ Nein |
| **Minor** Production | ❌ Nein | ❌ Nein |
| **Major** | ❌ Nein | ❌ Nein |

### Commit Messages

```
chore(deps): bump fastapi from 0.104.0 to 0.104.1
chore(deps-dev): bump pytest from 7.4.0 to 7.4.1
```

### Grouping

Ähnliche Updates werden gruppiert:

- **production-dependencies**: FastAPI, Pydantic, Uvicorn, etc.
- **security-dependencies**: Alle Security Updates
- **newman-dependencies**: Newman, Postman packages
- **actions-dependencies**: GitHub Actions

## 🔒 Security Updates

### Alerts

Dependabot erstellt Alerts für:
- Known vulnerabilities (CVEs)
- Malicious packages
- Dependency confusion attacks

### Automatische Security PRs

Kritische Security Updates werden sofort erstellt:
```
🔒 Security Update: bump django from 3.2.0 to 3.2.15
```

### Ignorierte Updates

Folgende werden ignoriert:
- Major Python Version Updates (Breaking Changes)
- Docker Base Image Major Updates

## 📊 Monitoring

### Insights

Dependabot Activity einsehen:
```
https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/network/updates
```

### Dependency Graph

Vollständige Übersicht:
```
https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/network/dependencies
```

## 🛠️ Manuelle Ausführung

### PRs manuell triggern

```bash
# Dependabot manuell auslösen
# Gehe zu: Insights → Dependency Graph → Dependabot
# Klicke "Check for updates"
```

### Konfiguration testen

```bash
# Mit Dependabot CLI (lokal)
npm install -g @dependabot/cli

dependabot update pip /path/to/repo
```

## 📝 Konfigurationsdatei

`.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    labels:
      - "dependencies"
      - "python"
```

## 🚨 Troubleshooting

### PRs werden nicht erstellt

1. Prüfe ob Dependabot aktiviert ist (Settings)
2. Prüfe ob `dependabot.yml` Syntax korrekt ist
3. Schaue in Security → Dependabot Alerts

### Konflikte bei Updates

```bash
# Lokale Konflikte lösen
git fetch origin
git checkout dependabot/pip/fastapi-0.105.0
git rebase main
```

### Zu viele PRs

- Limit in `dependabot.yml` anpassen: `open-pull-requests-limit: 5`
- Oder: Grouping verwenden für zusammengefasste Updates

## 📈 Best Practices

1. **Schnell mergen** - Patch Updates sind sicher
2. **Tests laufen lassen** - CI prüft vor Merge
3. **Major Updates reviewen** - Breaking Changes prüfen
4. **Security Updates priorisieren** - Sofort mergen
5. **Monatliche Reviews** - Dependencies aktuell halten

## 🔗 Weitere Ressourcen

- [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
- [Configuration Options](https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuration-options-for-the-dependabot.yml-file)
- [GitHub Blog: Dependabot](https://github.blog/tag/dependabot/)

## 🤝 Unterstützung

Bei Problemen:
1. [Dependabot Issues](https://github.com/dependabot/dependabot-core/issues)
2. [GitHub Support](https://support.github.com/)
