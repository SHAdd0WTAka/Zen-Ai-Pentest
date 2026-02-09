## [2.3.8] - 2026-02-06

### Fixed
- Restored 18 truncated workflow files with complete job definitions
- Fixed 6 YAML syntax errors in workflow files
- Restored complete PyPI release workflow with OIDC authentication
- Fixed multi-line string issues in telegram-notifications.yml

### Changed  
- Updated README badges to reflect current security status (100/100)
- All 50 workflows now pass YAML validation
# Changelog

All notable changes to Zen AI Pentest will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Repository health improvements (Issue #67)
  - Added comprehensive SUPPORT.md documentation
  - Added detailed architecture documentation (docs/ARCHITECTURE.md)
  - Added complete installation guide (docs/INSTALLATION.md)
  - Added markdown issue templates (bug_report.md, feature_request.md)
  - Enhanced pull request template with comprehensive checklist
  - Updated GitHub issue template configuration
- Enhanced CI/CD pipeline with security scanning
- New health check endpoints for monitoring

### Changed
- Improved README.md structure with table of contents
- Enhanced documentation organization
- Updated dependency versions for security patches

### Fixed
- Minor documentation typos and formatting issues

---

## [2.3.6] - 2026-02-06

### 🛡️ Security Fixes

#### Python Dependencies
- **requests** (CVE-2024-35195): Updated to >= 2.32.0
- **jinja2** (CVE-2024-56201, CVE-2024-56326): Updated to >= 3.1.5
- **cryptography** (CVE-2024-41985, CVE-2024-25185): Updated to >= 43.0.1

#### NPM Dependencies
- **jsonpath** (CVE-2025-61140): Updated to >= 1.2.0
- **webpack-dev-server** (CVE-2025-30360, CVE-2025-30359): Updated to >= 5.2.1

### ✨ New Features
- **Cache System**: Redis-backed caching with in-memory fallback
- **Auth Flow**: Complete authentication system in React dashboard
- **API Enhancements**: New PATCH /findings/{id} endpoint for updating findings

### 🔧 Code Quality
- Fixed 74+ Ruff linting errors across 252 files
- Added Bandit security configuration for pentesting tools
- Formatted all Python files with consistent style

### 🚀 CI/CD Improvements
- Reduced Python CI test matrix (Ubuntu: 3.11-3.13, Windows/macOS: 3.12 only)
- Added npm cache configuration for faster frontend builds
- Improved PyPI deployment workflow with deployment tracking

---

## [2.2.0] - 2026-02-05 (Q1 2026 Release)

### 🚀 New Features

#### React Dashboard
- Modern React 18 frontend with Tailwind CSS
- Real-time statistics and charts (Recharts)
- SIEM integration management UI
- Responsive design for mobile/tablet/desktop
- Production-ready build system

#### WebSocket v2.0
- Real-time updates for scan progress
- Room-based message routing (dashboard/scans/findings/notifications)
- Automatic reconnection with heartbeat
- User-specific notification channels

#### Report Export
- PDF generation with WeasyPrint
- Multiple templates: Executive, Technical, Compliance
- CSV export for findings data
- JSON export for API integration

#### SIEM Integration
- Splunk HTTP Event Collector (HEC) support
- Elasticsearch/Elastic SIEM integration
- Azure Sentinel / Log Analytics connector
- IBM QRadar REST API connector
- Batch event processing
- Threat intelligence queries

### 🔧 Improvements
- API v1.0 endpoints for SIEM management
- Enhanced test coverage (96 tests passing)
- Security fixes for CVE-2024-53981, CVE-2024-45492, CVE-2024-6239
- Improved risk engine accuracy
- Faster scan initialization
- Better memory management

### 📊 Statistics
- 96 unit tests passing
- 0 critical bugs
- 4 SIEM platforms supported
- 3 export formats available
- 20+ integrated security tools

---

## [2.1.0] - 2026-02-04 (Q1 2026 Release)

### 🚀 New Features

#### Autonomous Agent Improvements
- Enhanced ReAct pattern implementation
- Better error recovery and retry logic
- Improved tool selection algorithms
- Memory system optimizations

#### Risk Engine v2
- False positive reduction algorithms
- Business impact calculator
- CVSS 3.1 scoring support
- EPSS integration

#### CI/CD Integration
- GitHub Actions native support
- GitLab CI templates
- Jenkins pipeline integration
- SARIF output format

### Security
- Fixed CVE-2024-53981 (python-multipart)
- Fixed CVE-2024-45492 (weasyprint)
- Fixed CVE-2024-6239 (langchain-core)
- Enhanced input validation
- Improved authentication mechanisms

---

## [2.0.4] - 2026-02-04

### Fixed
- PyPI classifier error removed
- Version badge updated
- Architecture diagram added
- Documentation links fixed

---

## [2.0.0] - 2026-01-31

### 🚀 Initial Stable Release

#### Core Features
- AI-powered penetration testing framework
- Autonomous ReAct agent system
- Risk scoring and validation engine
- REST API with FastAPI
- WebSocket real-time updates
- Docker and Kubernetes support

#### Tools Integration
- Network scanning (Nmap, Masscan)
- Web testing (SQLMap, Gobuster, ZAP)
- Exploitation (Metasploit)
- Active Directory (BloodHound)

#### Reporting
- PDF report generation
- HTML dashboard
- JSON/XML export
- Slack/email notifications

---

## [1.0.0] - 2024-12-01

### Initial Development
- Project inception
- Core architecture design
- Basic agent implementation
- Initial tool integrations

---

## Release Notes Format

Each release may include the following types of changes:

- **Added** - New features
- **Changed** - Changes to existing functionality
- **Deprecated** - Soon-to-be removed features
- **Removed** - Removed features
- **Fixed** - Bug fixes
- **Security** - Security improvements

---

## Version Support Policy

| Version | Status | Support End Date |
|---------|--------|------------------|
| 2.2.x | Active | 2026-12-31 |
| 2.1.x | Maintenance | 2026-06-30 |
| 2.0.x | End of Life | 2026-03-31 |
| < 2.0 | Unsupported | - |

---

## How to Upgrade

### Docker Deployment
```bash
# Pull latest images
docker-compose pull

# Restart services
docker-compose up -d

# Run migrations
docker-compose exec api alembic upgrade head
```

### Local Installation
```bash
# Pull latest code
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Run migrations
alembic upgrade head
```

---

<p align="center">
  <sub>For detailed migration guides, see <a href="docs/MIGRATION.md">docs/MIGRATION.md</a></sub>
</p>

