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

### Sicherheitsstatus: ✅ CLEAN

**Letzter Scan:** 2026-02-24

```
✅ pip-audit: No known vulnerabilities found
✅ Snyk: All checks passing
✅ CodeQL: No new alerts
```

### Behobene Vulnerabilities

| CVE | Package | Alt | Neu | Fix Datum |
|-----|---------|-----|-----|-----------|
| CVE-2024-21503 | black | 24.1.1 | 26.1.0 | 2026-02-24 |
| CVE-2024-23342 | python-jose/ecdsa | 3.5.0/0.19.1 | PyJWT 2.11.0 | 2026-02-24 |
| PYSEC-2022-42969 | retry/py | 0.9.2/1.11.0 | tenacity 9.1.4 | 2026-02-24 |

### Dependency Änderungen

**Ersetzt:**
- `python-jose` + `ecdsa` → `PyJWT` (maintained, sicher)
- `retry` + `py` → `tenacity` (maintained, sicher)

**Gründe:**
- `ecdsa`: Projekt inaktiv, CVE seit 2024 ungefixt
- `py`: Projekt inaktiv, CVE seit 2022 ungefixt

## Monitoring

### Automatische Scans

- **Snyk:** Täglich um 06:00 UTC
- **CodeQL:** Bei jedem Push
- **pip-audit:** Vor jedem Release

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
- ✅ SECURITY.md vorhanden

---

**Letzte Aktualisierung:** 2026-02-24
**Nächste Review:** 2026-03-24
**Status:** ✅ All vulnerabilities resolved
