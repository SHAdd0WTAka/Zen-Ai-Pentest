# Statement of Applicability (SoA)

## ISO 27001 Requirement: 6.1.3

## Document Purpose

This Statement of Applicability defines which of the ISO 27001:2022 controls are applicable to Zen-AI-Pentest, justifies their inclusion/exclusion, and documents their implementation status.

---

## Document Control

- **Version**: 1.0
- **Date**: 2026-02-11
- **Owner**: @SHAdd0WTAka
- **Approver**: Project Owner
- **Classification**: Internal

---

## 1. Organizational Controls (A.5)

| Control | Title | Applicable | Justification | Status |
|---------|-------|------------|---------------|--------|
| A.5.1 | Policies for information security | ✅ YES | Required for governance | Implemented |
| A.5.2 | Information security roles | ✅ YES | @SHAdd0WTAka as owner, community roles defined | Implemented |
| A.5.3 | Segregation of duties | ❌ N/A | Single maintainer, compensated by review process | Justified |
| A.5.4 | Management responsibilities | ✅ YES | Owner reviews security posture quarterly | Implemented |
| A.5.5 | Contact with special interest groups | ✅ YES | CVE monitoring, security advisories | Implemented |
| A.5.6 | Information security in project management | ✅ YES | Security integrated in all PRs | Implemented |
| A.5.7 | Inventory of information and assets | ✅ YES | Asset: code, docs, community data | Implemented |
| A.5.8 | Acceptable use of information | ✅ YES | Code of Conduct, Contributing Guide | Implemented |
| A.5.9 | Inventory of information and assets | ✅ YES | GitHub as asset registry | Implemented |
| A.5.10 | Acceptable use of information | ✅ YES | Defined in CONTRIBUTING.md | Implemented |
| A.5.11 | Return of assets | ❌ N/A | No physical assets, code is open | Justified |
| A.5.12 | Classification of information | ✅ YES | Public (code) vs Internal (ops) | Implemented |
| A.5.13 | Labeling of information | ✅ YES | Labels in issues, PRs | Implemented |
| A.5.14 | Information transfer | ✅ YES | Encryption for sensitive transfers | Implemented |
| A.5.15 | Access control | ✅ YES | GitHub permissions, Discord roles | Implemented |
| A.5.16 | Identity management | ✅ YES | GitHub SSO, MFA enforced | Implemented |
| A.5.17 | Authentication information | ✅ YES | Token management procedures | Implemented |
| A.5.18 | Access rights | ✅ YES | RBAC on GitHub, Discord | Implemented |
| A.5.19 | Information security in supplier relationships | ⚠️ PARTIAL | Limited third-party deps, assessed | In Progress |
| A.5.20 | Addressing information security in agreements | ⚠️ PARTIAL | MIT License covers liability | Review Needed |
| A.5.21 | Managing information security in ICT services | ✅ YES | CI/CD security controls | Implemented |
| A.5.22 | Monitoring and review of supplier services | ⚠️ PARTIAL | Dependabot, security advisories | In Progress |
| A.5.23 | Information security for use of cloud services | ✅ YES | GitHub security features used | Implemented |
| A.5.24 | Planning and preparation for information security continuity | ✅ YES | Backup strategy documented | Implemented |
| A.5.25 | ICT readiness for continuity | ✅ YES | Distributed git = natural backup | Implemented |
| A.5.26 | Information security aspects of business continuity management | ✅ YES | Project resilience plan | Implemented |
| A.5.27 | Redundancies of information processing facilities | ✅ YES | GitHub + local redundancy | Implemented |
| A.5.28 | Requirements for availability of information systems | ✅ YES | SLA defined (best effort) | Implemented |
| A.5.29 | Privacy and protection of PII | ✅ YES | No telemetry, GDPR compliance | Implemented |
| A.5.30 | Independent review of information security | ⚠️ PARTIAL | Community audit, self-assessment | In Progress |
| A.5.31 | Identification of legal, statutory, regulatory and contractual requirements | ✅ YES | MIT License, GDPR compliance | Implemented |
| A.5.32 | Intellectual property rights | ✅ YES | MIT License, copyright headers | Implemented |
| A.5.33 | Protection of records | ✅ YES | Git history, signed commits | Implemented |
| A.5.34 | Privacy and protection of PII | ✅ YES | Min data collection, encryption | Implemented |
| A.5.35 | Independent review of information security | ⚠️ PARTIAL | Self-certification model | Review Needed |
| A.5.36 | Compliance with policies, rules and standards for information security | ✅ YES | CI enforces compliance | Implemented |
| A.5.37 | Documented operating procedures | ✅ YES | This documentation suite | Implemented |

---

## 2. People Controls (A.6)

| Control | Title | Applicable | Justification | Status |
|---------|-------|------------|---------------|--------|
| A.6.1 | Screening | ❌ N/A | Open community, merit-based | Justified |
| A.6.2 | Terms and conditions of employment | ❌ N/A | Volunteer contributors | Justified |
| A.6.3 | Information security awareness, education and training | ✅ YES | Security guidelines, Discord training | Implemented |
| A.6.4 | Disciplinary process | ❌ N/A | Code of Conduct enforcement | Justified |
| A.6.5 | Responsibilities after termination | ⚠️ PARTIAL | Access revocation on role change | In Progress |
| A.6.6 | Confidentiality or non-disclosure agreements | ⚠️ PARTIAL | Implicit via MIT License | Review Needed |
| A.6.7 | Remote working | ✅ YES | Fully remote project | Implemented |
| A.6.8 | Information security event reporting | ✅ YES | Security.md, issue templates | Implemented |

---

## 3. Physical Controls (A.7)

| Control | Title | Applicable | Justification | Status |
|---------|-------|------------|---------------|--------|
| A.7.1 | Physical security perimeters | ✅ YES | Developer workstations | Implemented |
| A.7.2 | Physical entry controls | ✅ YES | Personal device security | Implemented |
| A.7.3 | Securing offices, rooms and facilities | ❌ N/A | No physical office | Justified |
| A.7.4 | Physical security monitoring | ✅ YES | Device tracking, Find My | Implemented |
| A.7.5 | Protecting against physical and environmental threats | ✅ YES | Hardware maintenance | Implemented |
| A.7.6 | Working in secure areas | ❌ N/A | N/A for remote work | Justified |
| A.7.7 | Clear desk and clear screen | ✅ YES | Screen lock policy | Implemented |
| A.7.8 | Equipment siting and protection | ✅ YES | Personal device care | Implemented |
| A.7.9 | Security of assets off-premises | ✅ YES | Laptop encryption, VPN | Implemented |
| A.7.10 | Storage media | ✅ YES | Encrypted backups | Implemented |
| A.7.11 | Supporting utilities | ✅ YES | UPS for workstations | Implemented |
| A.7.12 | Cabling security | ✅ YES | Home network security | Implemented |
| A.7.13 | Equipment maintenance | ✅ YES | Regular device updates | Implemented |
| A.7.14 | Secure disposal of equipment | ✅ YES | Secure wipe procedures | Implemented |

---

## 4. Technological Controls (A.8)

| Control | Title | Applicable | Justification | Status |
|---------|-------|------------|---------------|--------|
| A.8.1 | User endpoint devices | ✅ YES | Device encryption, EDR | Implemented |
| A.8.2 | Privileged access rights | ✅ YES | GitHub admin protection | Implemented |
| A.8.3 | Information access restriction | ✅ YES | Code review required | Implemented |
| A.8.4 | Access to source code | ✅ YES | Branch protection, reviews | Implemented |
| A.8.5 | Secure authentication | ✅ YES | MFA, strong passwords | Implemented |
| A.8.6 | Capacity management | ✅ YES | GitHub quotas monitored | Implemented |
| A.8.7 | Protection against malware | ✅ YES | Defender, scanning | Implemented |
| A.8.8 | Management of technical vulnerabilities | ✅ YES | Dependabot, pip-audit | Implemented |
| A.8.9 | Configuration management | ✅ YES | Infrastructure as Code | Implemented |
| A.8.10 | Information deletion | ✅ YES | Data retention policy | Implemented |
| A.8.11 | Data masking | ❌ N/A | No production data used | Justified |
| A.8.12 | Data leakage prevention | ✅ YES | Pre-commit hooks, DLP | Implemented |
| A.8.13 | Information backup | ✅ YES | Git + cloud backup | Implemented |
| A.8.14 | Redundancy of information processing facilities | ✅ YES | Distributed by design | Implemented |
| A.8.15 | Logging | ✅ YES | CI/CD logs, audit trail | Implemented |
| A.8.16 | Monitoring activities | ✅ YES | GitHub security alerts | Implemented |
| A.8.17 | Clock synchronization | ✅ YES | NTP on all systems | Implemented |
| A.8.18 | Use of privileged utility programs | ✅ YES | Admin access limited | Implemented |
| A.8.19 | Installation of software on operational systems | ✅ YES | Approved packages only | Implemented |
| A.8.20 | Network security management | ✅ YES | VPN, firewall, zero trust | Implemented |
| A.8.21 | Security of network services | ✅ YES | TLS, cert management | Implemented |
| A.8.22 | Segregation in networks | ⚠️ PARTIAL | Development isolated | In Progress |
| A.8.23 | Web filtering | ❌ N/A | Not applicable | Justified |
| A.8.24 | Use of cryptography | ✅ YES | TLS, encryption at rest | Implemented |
| A.8.25 | Secure development life cycle | ✅ YES | DevSecOps practices | Implemented |
| A.8.26 | Application security requirements | ✅ YES | Security requirements in issues | Implemented |
| A.8.27 | Secure system architecture and engineering principles | ✅ YES | Security by design | Implemented |
| A.8.28 | Secure coding | ✅ YES | Bandit, pre-commit | Implemented |
| A.8.29 | Security testing in development and acceptance | ✅ YES | CI security tests | Implemented |
| A.8.30 | Outsourced development | ❌ N/A | All development in-house | Justified |
| A.8.31 | Separation of development, test and production environments | ✅ YES | Separate branches, envs | Implemented |
| A.8.32 | Change management | ✅ YES | GitHub PR workflow | Implemented |
| A.8.33 | Test information | ✅ YES | Synthetic test data | Implemented |
| A.8.34 | Protection of information systems during audit testing | ✅ YES | Read-only audit access | Implemented |

---

## Summary

| Category | Total | Applicable | Excluded | Partial | % Applicable |
|----------|-------|------------|----------|---------|--------------|
| Organizational (A.5) | 37 | 28 | 4 | 5 | 89% |
| People (A.6) | 8 | 4 | 3 | 1 | 63% |
| Physical (A.7) | 14 | 11 | 3 | 0 | 79% |
| Technological (A.8) | 34 | 29 | 5 | 1 | 88% |
| **Total** | **93** | **72** | **15** | **7** | **85%** |

---

## Justification Notes

### Excluded Controls (Not Applicable)

1. **A.5.3, A.5.11**: Single maintainer model - compensated by mandatory review
2. **A.6.1, A.6.2, A.6.4**: Open community - merit-based contribution model
3. **A.7.3, A.7.6**: No physical office - fully remote project
4. **A.8.11**: No production data in test environments
5. **A.8.23, A.8.30**: Not applicable to project structure

### Partial Controls

1. **A.5.19-A.5.22**: Supply chain - ongoing improvement via SBOM
2. **A.5.30, A.5.35**: Independent review - self-certification with community audit
3. **A.8.22**: Network segmentation - virtual isolation implemented

---

## Approval

This Statement of Applicability is approved for implementation:

**Approved By**: @SHAdd0WTAka
**Date**: 2026-02-11
**Review Cycle**: Annual
