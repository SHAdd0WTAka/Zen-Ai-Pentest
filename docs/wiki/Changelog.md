# Changelog

Alle wichtigen Änderungen an diesem Projekt werden hier dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
und dieses Projekt folgt [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Repository erstellt:** 29. Januar 2026

---

## [Unreleased]

### Added
- GitHub App Authentication mit automatischer Token-Generierung
- Snyk Security Scanning Workflow
- Pre-commit Hooks für Code-Qualität
- Umfassende Wiki-Dokumentation (16 Seiten)
- Obsidian Vault Integration für Secrets
- PyJWT Migration (CVE-2024-23342 Fix)
- Dependency Review Workflow
- API Models für CI/CD-Kompatibilität

### Security
- CVE-2024-23342 (python-jose ECDSA timing attack) - Migration zu PyJWT
- CVE-2024-33663 (PyJWT Algorithm Confusion) - Fixed in PyJWT>=2.8.0
- CVE-2024-21503 (black ReDoS) - black>=26.1.0
- PYSEC-2022-42969 (py ReDoS) - Migration von retry zu tenacity

---

## [3.0.0] - 2026-02-19

### Added
- Multi-Agent System mit 11 spezialisierten Personas
- ReAct Pattern für autonome Entscheidungsfindung
- Docker Sandbox für sichere Tool-Ausführung
- WebSocket API für Real-time Updates
- Cloudflare Pages Deployment
- GitHub Actions Marketplace Integration
- Kimi Agent 100 Integration

### Changed
- Migration von Flask zu FastAPI
- Neue State Machine für Agent Workflows
- Verbesserte Risk Engine mit CVSS/EPSS

### Security
- JWT-based Authentication
- Role-Based Access Control (RBAC)
- Private IP Blocking
- Resource Limits für alle Tools
- CodeQL Alerts behoben (Script Injection, Clear-text logging)

---

## [2.3.9] - 2026-02-06

### Fixed
- PyPI publishing mit API Token
- YAML Syntax Errors in 6 Workflow-Dateien
- 18 truncierte Workflow-Dateien wiederhergestellt

---

## [2.3.8] - 2026-02-06

### Added
- Automated release notes and changelog
- Concurrency für 25 Workflows

### Changed
- Workflow Optimierung und Deduplizierung
- Badges aktualisiert

### Security
- esbuild CVE behoben
- Frontend npm vulnerabilities behoben
- jsonpath und webpack-dev-server Updates

---

## [2.3.7] - 2026-02-06

### Added
- PyPI release workflow mit deployment tracking
- API Dokumentation für v2.3.6

### Changed
- Python CI Test Matrix reduziert für schnellere Builds
- Docker Base Image auf Python 3.12 aktualisiert

### Security
- Bandit Konfiguration für Pentesting-Tools
- npm vulnerabilities (jsonpath, webpack-dev-server)

---

## [2.3.6] - 2026-02-06

### Changed
- Ruff linting errors behoben
- Frontend build in CI pipeline gefixt

---

## [2.3.5] - 2026-02-06

### Added
- Cache System mit Redis Support
- Auth Flow Verbesserungen
- API Enhancements

### Fixed
- TypeScript types in AgentMonitor.tsx

---

## [2.3.1] - 2026-02-05

### Fixed
- Workflow Stabilität und Security

---

## [2.3.0] - 2026-02-05

### Added
- Security Scanning Action
- GitHub Actions Improvements

---

## [2.2.0] - 2026-02-04

### Added
- Workflow concurrency controls
- Deduplication improvements

---

## [2.1.0] - 2026-02-04

### Added
- Enhanced CI/CD pipeline
- Status check workflows

---

## [2.0.4] - 2026-02-04

### Fixed
- npm ci error in CI workflow
- Deployment tracking improvements

---

## [2.0.3] - 2026-02-04

### Added
- PyPI workflow mit deployment tracking
- Security improvements

---

## [2.0.2] - 2026-02-04

### Added
- Status check workflow

---

## [2.0.1] - 2026-02-03

### Fixed
- Initial bugfixes for v2.0

---

## [2.0.0] - 2026-02-03

### Added
- Agent Coordinator V3
- Workflow Engine mit DAG Support
- False Positive Engine
- LLM Voting System

### Changed
- Refactored Tool Executor
- Neue Datenbank-Models
- Verbesserte Caching Layer

### Removed
- Legacy Agent System (V1)
- Old CLI Interface

---

## [1.0.0] - 2026-01-31

### Added
- Initial Release
- Basic API (FastAPI)
- Nmap Integration
- Simple Agent System
- PostgreSQL Support
- Foundation Release

---

## Kategorien

- **Added** - Neue Features
- **Changed** - Änderungen an bestehenden Features
- **Deprecated** - Features die entfernt werden
- **Removed** - Entfernte Features
- **Fixed** - Bugfixes
- **Security** - Security-relevante Änderungen

---

## Alle Tags & Releases

| Tag | Datum | Beschreibung |
|-----|-------|--------------|
| v3.0.0 | 2026-02-19 | Kimi Agent 100 Integration |
| v2.3.9 | 2026-02-06 | PyPI publishing fixes |
| v2.3.8 | 2026-02-06 | Workflow concurrency |
| v2.3.7 | 2026-02-06 | Bandit & npm security |
| v2.3.6 | 2026-02-06 | Ruff linting fixes |
| v2.3.5 | 2026-02-06 | Redis cache system |
| v2.3.4 | 2026-02-04 | PyPI workflow fixes |
| v2.3.3 | 2026-02-04 | npm ci fixes |
| v2.3.2 | 2026-02-04 | Status checks |
| v2.3.1 | 2026-02-05 | Workflow stability |
| v2.3.0 | 2026-02-05 | Security Scanning Action |
| v2.2.0 | 2026-02-04 | Concurrency controls |
| v2.2.0-rc1 | 2026-02-03 | Release Candidate |
| v2.1.0 | 2026-02-04 | Enhanced CI/CD |
| v2.0.4 | 2026-02-04 | npm ci fixes |
| v2.0.3 | 2026-02-04 | Deployment tracking |
| v2.0.2 | 2026-02-04 | Status check workflow |
| v2.0.1 | 2026-02-03 | Bugfixes |
| v2.0.0 | 2026-02-03 | Agent Coordinator V3 |
| v1.0.0 | 2026-01-31 | Foundation Release |

---

## Projekt-Timeline

```
2026-01-29 │ Repository erstellt
           │
2026-01-31 ├─ v1.0.0 - Foundation Release
           │
2026-02-03 ├─ v2.0.0 - Agent Coordinator V3
           │
2026-02-04 ├─ v2.1.0 - Enhanced CI/CD
           │  ├─ v2.2.0 - Concurrency Controls
           │  ├─ v2.3.0 - Security Scanning
           │  └─ v2.3.5-9 - Stabilität & PyPI
           │
2026-02-19 ├─ v3.0.0 - Kimi Agent 100 Integration
           │
2026-02-24 └─ [Unreleased] - GitHub App Auth, Wiki, Security Fixes
```

---

**Hinweis:** Dieses Changelog wird automatisch aus den GitHub Releases und Tags generiert.

[← Zurück zur Startseite](Home)
