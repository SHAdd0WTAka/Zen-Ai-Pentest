# Changelog

All notable changes to Zen AI Pentest will be documented in this file.

## [2.2.0] - 2026-04-XX (Q2 2026 Release)

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

### 🔧 Improvements
- API v1.0 endpoints for SIEM management
- Enhanced test coverage (96 tests passing)
- Security fixes for CVE-2024-53981, CVE-2024-45492, CVE-2024-6239

### 📊 Statistics
- 96 unit tests passing
- 0 critical bugs
- 4 SIEM platforms supported
- 3 export formats available

---

## [2.1.0] - 2026-02-04 (Q1 2026 Release)

### 🚀 New Features

#### SIEM Integration
- Splunk HTTP Event Collector (HEC) support
- Elasticsearch/Elastic SIEM integration
- Azure Sentinel / Log Analytics connector
- IBM QRadar REST API connector
- Batch event processing
- Threat intelligence queries

#### REST API v1.0
- `/api/v1/siem/connect` - Connect to SIEM
- `/api/v1/siem/status` - Get connection status
- `/api/v1/siem/events` - Send security events
- `/api/v1/siem/events/batch` - Batch event ingestion
- `/api/v1/siem/query/{name}` - Query threat intel

### Security
- Fixed CVE-2024-53981 (python-multipart)
- Fixed CVE-2024-45492 (weasyprint)
- Fixed CVE-2024-6239 (langchain-core)

---

## [2.0.4] - 2026-02-04

### Fixed
- PyPI classifier error removed
- Version badge updated
- Architecture diagram added

---

## [2.0.0] - 2026-01-31

### Initial Release
- Core pentesting framework
- AI-powered agents
- Risk scoring engine
- REST API foundation
- Docker support

---

## Release Notes Format

- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements
