# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Enterprise setup complete (Branch Protection, CI/CD, Security)
- Automated Dependabot PR merging workflow
- Architecture Decision Records (ADRs) documentation structure
- GitHub Pages documentation site
- Wiki auto-sync from docs folder

### Security
- Branch protection enabled for master branch
- Required PR reviews (1 approval minimum)
- CODEOWNERS review required for sensitive files
- Force pushes blocked
- Secret scanning enabled
- CodeQL analysis configured

## [1.0.0] - 2024-06-30

### Added
- Multi-LLM Orchestration (DuckDuckGo, OpenRouter, ChatGPT, Claude)
- Multi-Agent System (Clawed/Moltbot-style collaboration)
- CVE Database with 1000+ entries
- Ransomware IOC Database (NotPetya, WannaCry, Locky, etc.)
- SQL Injection Payload Library (50+ payloads, 6 DB types)
- Nuclei Template Integration
- Post-Scan Workflow (PTES methodology)
- Docker support (standard, pentest, shield variants)
- ProtonVPN integration
- Zen Shield container security
- REST API (FastAPI-based)
- WebSocket support for real-time updates
- Redis caching layer
- AsyncIO architecture
- Plugin system
- OSINT module

### Security
- Input validation and sanitization
- API key management (config.json)
- Rate limiting
- Audit logging
- Secure configuration handling

## [0.9.0] - 2024-03-15

### Added
- Initial multi-agent prototype
- Basic LLM routing
- CVE database foundation
- CLI interface
- Report generation (Markdown, JSON)

### Changed
- Refactored from single-agent to multi-agent

## [0.8.0] - 2024-01-20

### Added
- Initial release
- Basic reconnaissance module
- Single LLM backend (DuckDuckGo)
- Basic vulnerability analysis

---

## Release Notes Format

Each release should include:

### Added
- New features

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Now removed features

### Fixed
- Bug fixes

### Security
- Security improvements and vulnerabilities fixed

---

## Versioning Guide

- **MAJOR** (X.0.0): Breaking changes, new architecture
- **MINOR** (0.X.0): New features, backwards compatible
- **PATCH** (0.0.X): Bug fixes, security patches

## Planned Releases

- **v1.1.0** (Q3 2024): Performance optimizations, caching, rate limiting
- **v2.0.0** (Q4 2024): Enterprise features, Web UI, ML integration

---

*For detailed migration guides between versions, see [docs/MIGRATION.md](docs/MIGRATION.md)*
