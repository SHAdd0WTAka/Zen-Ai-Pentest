# Changelog

Alle wichtigen Änderungen an diesem Projekt werden hier dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt folgt [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Added
- GitHub App Authentication mit automatischer Token-Generierung
- Snyk Security Scanning Workflow
- Pre-commit Hooks für Code-Qualität
- Umfassende Wiki-Dokumentation
- Obsidian Vault Integration für Secrets

### Security
- CodeQL Alerts behoben (Script Injection, Clear-text logging)
- RBAC Permissions gehärtet
- Kubernetes Security Policies aktualisiert

## [3.0.0] - 2026-02-24

### Added
- Multi-Agent System mit 11 spezialisierten Personas
- ReAct Pattern für autonome Entscheidungsfindung
- Docker Sandbox für sichere Tool-Ausführung
- WebSocket API für Real-time Updates
- Cloudflare Pages Deployment
- GitHub Actions Marketplace Integration

### Changed
- Migration von Flask zu FastAPI
- Neue State Machine für Agent Workflows
- Verbesserte Risk Engine mit CVSS/EPSS

### Security
- JWT-based Authentication
- Role-Based Access Control (RBAC)
- Private IP Blocking
- Resource Limits für alle Tools

## [2.5.0] - 2025-12-15

### Added
- Nuclei Integration für CVE Detection
- SQLMap Integration mit Safety Controls
- Subdomain Enumeration mit Subfinder
- HTTPX für schnelles HTTP Probing

### Fixed
- Memory Leaks in Agent Orchestrator
- Timeout Handling bei langen Scans
- Docker Container Cleanup

## [2.0.0] - 2025-10-01

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

## [1.5.0] - 2025-08-20

### Added
- First AI Personas (Recon, Exploit, Report)
- Basic MCP Server
- CLI Tools (k-recon, k-exploit)
- Benchmark Suite

### Security
- Initial Safety Controls
- Docker Sandbox (basic)

## [1.0.0] - 2025-06-01

### Added
- Initial Release
- Basic API (Flask)
- Nmap Integration
- Simple Agent System
- PostgreSQL Support

---

## Kategorien

- **Added** - Neue Features
- **Changed** - Änderungen an bestehenden Features
- **Deprecated** - Features die entfernt werden
- **Removed** - Entfernte Features
- **Fixed** - Bugfixes
- **Security** - Security-relevante Änderungen
