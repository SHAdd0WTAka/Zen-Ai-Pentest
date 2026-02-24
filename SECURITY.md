# Security Policy

## Sicherheitsstandards

Zen-AI-Pentest folgt strikten Sicherheitsstandards:

- ✅ Alle Code-Änderungen durch Pre-commit Hooks
- ✅ Automatische Snyk Scans bei jedem Push
- ✅ CodeQL Analyse für statische Code-Analyse
- ✅ pip-audit für Dependency Scanning
- ✅ Private IP Blocking für alle Tools
- ✅ Docker Sandbox für Tool-Ausführung

## Aktuelle Sicherheitslage

### Gefixte Vulnerabilities (letzte 24h)

| Package | Alt | Neu | Issue |
|---------|-----|-----|-------|
| black | 24.1.1 | 26.1.0 | CVE-2024-21503 (ReDoS) |
| tqdm | 4.66.x | 4.67.3 | Injection |

### Bekannte Vulnerabilities ohne Fix

Die folgenden Vulnerabilities haben **keine verfügbaren Fixes**:

#### 1. ecdsa 0.19.1 - CVE-2024-23342

- **Severity:** Medium
- **Beschreibung:** Minerva timing attack on P-256 curve
- **Verwendet von:** python-jose (JWT-Handling)
- **Risiko:** Niedrig (nur interne JWT-Signierung)
- **Grund:** Projekt betrachtet Side-Channel als out of scope
- **Workaround:** Keiner verfügbar, wird überwacht

#### 2. py 1.11.0 - PYSEC-2022-42969

- **Severity:** Low
- **Beschreibung:** ReDoS via Subversion repository
- **Verwendet von:** retry (Dev-Dependency für pysnyk)
- **Risiko:** Niedrig (nur in Dev-Tools verwendet)
- **Grund:** Kein neueres Release verfügbar
- **Workaround:** Keiner verfügbar, wird überwacht

## Risikobewertung

Die verbleibenden Vulnerabilities stellen **kein kritisches Risiko** dar:

1. **ecdsa:** Nur für interne JWT-Signierung verwendet, keine externe Angriffsfläche
2. **py:** Nur in Dev-Dependencies (pysnyk), nicht in Production

## Monitoring

### Automatische Scans

- **Snyk:** Täglich um 06:00 UTC
- **CodeQL:** Bei jedem Push
- **pip-audit:** Manuelle Prüfung vor Releases

### Dashboards

- [GitHub Security](https://github.com/SHAdd0WTAka/zen-ai-pentest/security)
- [Snyk Dashboard](https://app.snyk.io/org/shadd0wtaka/projects)

## Melden von Sicherheitsproblemen

**Nicht öffentlich melden!**

Bei Sicherheitsvorfällen:
1. Security Advisory erstellen (privat)
2. Oder Email: shadd0wtaka@protonmail.com

## Sicherheitsmaßnahmen

### Code-Sicherheit
- Pre-commit Hooks (black, isort, flake8, bandit)
- Secret Detection (detect-secrets)
- Type Checking (mypy)

### Dependency-Sicherheit
- Snyk Monitoring
- pip-audit Scans
- Automated Dependabot Updates

### Runtime-Sicherheit
- Docker Sandbox für alle Tools
- Private IP Blocking
- Resource Limits (CPU, Memory, Time)
- Read-only Filesysteme

## Compliance

- ✅ OpenSSF Best Practices (passing)
- ✅ CodeQL aktiviert
- ✅ Dependabot aktiviert
- ✅ Snyk aktiviert
- ✅ Branch Protection für main

---

**Letzte Aktualisierung:** 2026-02-24
**Nächste Review:** 2026-03-24
