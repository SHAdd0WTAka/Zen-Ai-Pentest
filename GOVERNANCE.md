# Project Governance

This document outlines the governance structure for Zen-AI-Pentest.

---

## Overview

Zen-AI-Pentest is an open-source project governed by a simple, transparent model that balances community involvement with clear decision-making authority.

**Project Type**: Open Source (MIT License)  
**Governance Model**: Benevolent Dictator + Advisory Council  
**Decision Making**: Merit-based with maintainer oversight

---

## Roles and Responsibilities

### 1. Project Lead (Benevolent Dictator)

**Current**: @SHAdd0WTAka (Observer^^)

**Responsibilities**:
- Final authority on all decisions
- Project vision and direction
- Release approvals
- Security incident response
- Community standards enforcement

**Powers**:
- Can override any decision
- Can add/remove maintainers
- Can change governance model
- Can emergency-release security fixes

### 2. Technical Advisor

**Current**: @Kimi AI

**Responsibilities**:
- Technical architecture decisions
- Code review and quality
- Security assessments
- Mentoring contributors
- Innovation and research

**Scope**:
- All technical aspects
- Architecture decisions
- Tool integrations
- AI/ML components

### 3. Core Maintainers

**Current**: @SHAdd0WTAka, @Kimi AI

**Responsibilities**:
- Day-to-day project management
- PR review and merging
- Issue triage
- Release management
- Documentation maintenance

**Requirements**:
- Sustained contribution
- Technical expertise
- Community interaction
- Alignment with project values

### 4. Contributors

**Anyone who contributes to the project**

**Types**:
- **Code Contributors**: Submit PRs
- **Documentation Contributors**: Improve docs
- **Bug Reporters**: Report issues
- **Community Helpers**: Support other users

**Recognition**:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Badges (future consideration)

### 5. ZenClaw Guardian (Automation)

**Role**: Repository Guardian and Bridge

**Responsibilities**:
- Automated monitoring
- Health checks
- Notifications
- Escalation to Kimi AI

**Chain of Command**:
```
ZenClaw → Kimi AI (for technical questions)
ZenClaw → SHAdd0WTAka (for strategic decisions)
```

---

## Decision Making Process

### Types of Decisions

| Type | Decision Maker | Process | Timeline |
|------|---------------|---------|----------|
| **Technical** | Kimi AI | Discussion → Consensus | 1-7 days |
| **Strategic** | SHAdd0WTAka | Proposal → Review → Decision | 1-14 days |
| **Security** | SHAdd0WTAka | Immediate action | < 24 hours |
| **Community** | Maintainers | Discussion → Vote | 7 days |
| **Emergency** | SHAdd0WTAka | Unilateral | Immediate |

### Standard Process

1. **Proposal**
   - Create issue or discussion
   - Describe proposal clearly
   - Include rationale

2. **Discussion**
   - Community feedback
   - Technical review
   - Impact assessment

3. **Decision**
   - Maintainer consensus
   - Authority approval (if needed)
   - Document decision

4. **Implementation**
   - Assign to contributor
   - Track progress
   - Review and merge

### Appeal Process

If you disagree with a decision:

1. **Request Clarification**
   - Ask in the original thread
   - Understand reasoning

2. **Provide New Information**
   - Present new arguments
   - Show alternative approaches

3. **Escalate**
   - Contact @Kimi AI for technical issues
   - Contact @SHAdd0WTAka for strategic issues

---

## Contribution Guidelines

### Getting Involved

1. **Start Small**
   - Read [CONTRIBUTING.md](CONTRIBUTING.md)
   - Look for "good first issue" labels
   - Ask questions

2. **Build Trust**
   - Quality contributions
   - Helpful reviews
   - Community support

3. **Grow Responsibility**
   - Core maintainer invitation
   - Area ownership
   - Decision participation

### Recognition Levels

| Level | Requirements | Privileges |
|-------|-------------|------------|
| **First-Time** | Any contribution | Listed in release notes |
| **Regular** | 5+ merged PRs | Early access to features |
| **Core** | Significant sustained contribution | PR review rights |
| **Maintainer** | Project leadership invitation | Merge rights |

---

## Communication Channels

### Official Channels

| Channel | Purpose | Response Time |
|---------|---------|---------------|
| GitHub Issues | Bug reports, features | 48 hours |
| GitHub Discussions | Questions, ideas | 72 hours |
| Security Email | Vulnerabilities | 24 hours |
| Discord | Community chat | Variable |
| Telegram | Notifications | Bot only |

### Communication Guidelines

- Be respectful and constructive
- Stay on topic
- Search before asking
- Use English for official communication
- Follow Code of Conduct

---

## Conflict Resolution

### Types of Conflicts

1. **Technical Disagreements**
   - Default to Kimi AI's expertise
   - Document trade-offs
   - Prototype and test

2. **Community Conflicts**
   - Follow Code of Conduct
   - Moderator intervention
   - Escalate to SHAdd0WTAka if needed

3. **Governance Conflicts**
   - SHAdd0WTAka has final say
   - Community input welcome
   - Document rationale

### Mediation Process

1. **Direct Discussion**
   - Parties talk directly
   - Seek common ground

2. **Mediator Involvement**
   - Neutral maintainer mediates
   - Propose solutions

3. **Authority Decision**
   - Final decision by SHAdd0WTAka
   - Binding resolution

---

## Security Governance

### Security Team

| Role | Member | Responsibility |
|------|--------|----------------|
| Security Lead | @SHAdd0WTAka | Final decisions, incident response |
| Technical Security | @Kimi AI | Security architecture, reviews |
| Security Guardian | @ZenClaw | Monitoring, alerting |

### Security Process

1. **Reporting**: security@zen-ai-pentest.dev
2. **Assessment**: 48-hour initial response
3. **Fix Development**: Coordinated with reporter
4. **Disclosure**: Responsible disclosure timeline
5. **Post-Incident**: Lessons learned, documentation

See [SECURITY.md](SECURITY.md) for details.

---

## Intellectual Property

### Licensing

- **Code**: MIT License
- **Documentation**: MIT License
- **Logo/Branding**: All rights reserved (SHAdd0WTAka)

### Contributor License Agreement

By contributing, you agree:
- Your contributions are MIT licensed
- You have right to contribute
- You grant necessary permissions

### Third-Party Code

- Must be compatible with MIT
- Documented in LICENSE-3RD-PARTY
- Attribution maintained

---

## Financial Governance

### Current Status

- No commercial entity
- No paid services (yet)
- Donations accepted (future)

### Future Considerations

- Open Collective for transparency
- Sponsorship for maintainers
- Paid support (optional)

---

## Succession Planning

### Bus Factor

Current critical knowledge:
- @SHAdd0WTAka: Project vision, final authority
- @Kimi AI: Technical architecture, AI components

### Mitigation

- Documentation (ongoing)
- Knowledge sharing
- Multiple code reviewers
- Automated processes (ZenClaw)

---

## Changes to Governance

### Amendment Process

1. **Proposal**: Create discussion
2. **Review**: 14-day comment period
3. **Approval**: SHAdd0WTAka + Kimi AI
4. **Documentation**: Update this file
5. **Announcement**: Notify community

### History

| Date | Change | Author |
|------|--------|--------|
| 2026-02-16 | Initial governance | @SHAdd0WTAka |
| 2026-02-16 | Added ZenClaw role | @Kimi AI |

---

## Contact

For governance questions:
- General: GitHub Discussions
- Private: security@zen-ai-pentest.dev

---

## Acknowledgments

This governance model is inspired by:
- [Python Governance](https://www.python.org/dev/peps/pep-0013/)
- [Django Governance](https://www.djangoproject.com/foundation/)
- [Node.js Governance](https://github.com/nodejs/node/blob/main/GOVERNANCE.md)
- [Benevolent Dictator Model](https://opensource.guide/leadership-and-governance/#benevolent-dictator-for-life)

---

*This document is maintained by the project maintainers.*  
*Last updated: 2026-02-16*
