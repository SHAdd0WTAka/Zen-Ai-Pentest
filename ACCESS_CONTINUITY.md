# Access Continuity Plan

This document describes how the Zen-AI-Pentest project ensures continuity if key personnel become unavailable.

## Overview

The project maintains a bus factor of 2 or more to ensure continued operation even if any single person becomes unavailable.

## Current Bus Factor

**Current Bus Factor: 2**

- Primary: ATAKAN_AYDIN (Project Maintainer)
- Backup: GitHub Organization + Designated Successor Plan

## Critical Assets

### 1. GitHub Repository Access

**Primary Owner:** ATAKAN_AYDIN (@SHAdd0WTAka)

**Backup Plan:**
- Repository is public (can be forked by community)
- GitHub Organization structure allows adding new maintainers
- Regular backups pushed to multiple locations

**Successor Procedure:**
1. GitHub allows account recovery through verified email
2. If account cannot be recovered, community can fork and continue
3. Designated successor can be granted access in advance

### 2. Domain Names & DNS

**Primary:** ATAKAN_AYDIN controls domain registration

**Backup Plan:**
- Domain registrar account recovery via email
- DNS managed via Cloudflare with backup access
- Documentation of all DNS settings in repository

### 3. Secrets and Credentials

**Storage Location:** Obsidian Vault (local, encrypted)

**Backup Plan:**
- All critical secrets stored in encrypted vault
- Recovery instructions documented offline
- Emergency contact has vault access instructions

**Critical Secrets List:**
- GitHub Personal Access Tokens
- Cloudflare API Keys
- Docker Hub Credentials
- PyPI API Token
- Codecov Token

### 4. Infrastructure

**Current Infrastructure:**
- GitHub Pages (documentation)
- GitHub Actions (CI/CD)
- Docker Hub (container registry)

**Backup Plan:**
- All infrastructure as code in repository
- Can be recreated by any maintainer
- No single point of failure

## Emergency Procedures

### Scenario 1: Project Maintainer Unavailable

**Timeline:** Response within 1 week

**Actions:**
1. **Day 1-3:** Attempt contact through all known channels
2. **Day 4-7:** Core contributors assess situation
3. **Week 2:**
   - If temporary: Wait for return
   - If permanent: Activate successor plan

**Successor Activation:**
1. Community discussion on GitHub
2. Vote/Consensus on new maintainer
3. Transfer repository ownership (if possible)
4. Or fork and continue under new leadership

### Scenario 2: Critical Security Issue

**Timeline:** Response within 24 hours

**Actions:**
1. Any core contributor can create security advisory
2. Security Team Lead (or backup) coordinates fix
3. Emergency release can be made by any core contributor
4. Community notification via security channel

### Scenario 3: Infrastructure Failure

**Timeline:** Response within 48 hours

**Actions:**
1. Use Infrastructure as Code to recreate
2. Community contributors can help
3. Switch to backup services if needed

## Prevention Measures

### Regular Activities

- [ ] Monthly review of access continuity plan
- [ ] Quarterly backup verification
- [ ] Annual succession planning review

### Documentation

All procedures documented in:
- This file (ACCESS_CONTINUITY.md)
- GOVERNANCE.md
- ROLES.md
- Encrypted recovery notes (offline)

### Communication

- Primary: GitHub Issues/Discussions
- Emergency: Email to core contributors
- Security: security@zen-ai-pentest.dev

## Contact Information

**Current Project Maintainer:**
- Name: ATAKAN_AYDIN
- GitHub: @SHAdd0WTAka
- Email: maintainer [at] zen-ai-pentest.dev

**Emergency Contact:**
- (Stored in encrypted recovery notes)

---

*Last updated: 2026-02-25*
*Next review: 2026-03-25*
