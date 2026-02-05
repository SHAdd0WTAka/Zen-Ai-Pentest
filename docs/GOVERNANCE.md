# Zen AI Pentest Governance

> This document describes the governance model for the Zen AI Pentest project.

---

## Overview

Zen AI Pentest follows an **open governance** model that balances community participation with clear decision-making processes. We believe in transparency, meritocracy, and community-driven development.

### Principles

1. **Transparency** - All decisions and discussions are public
2. **Meritocracy** - Recognition based on contribution quality
3. **Inclusivity** - Everyone can contribute and participate
4. **Consensus** - Decisions made through discussion and agreement
5. **Accountability** - Clear responsibilities and expectations

---

## Decision Making Process

### Types of Decisions

| Type | Description | Decision Maker | Timeline |
|------|-------------|----------------|----------|
| **Trivial** | Typos, docs fixes, trivial bugs | Any Maintainer | Immediate |
| **Minor** | Small features, non-breaking changes | Maintainer consensus | 3-5 days |
| **Major** | New features, breaking changes | Community vote | 1-2 weeks |
| **Strategic** | Roadmap, architecture, policies | Steering Committee | 2-4 weeks |

### Decision Making Steps

```
┌─────────────────────────────────────────────────────────────────┐
│                     DECISION FLOW                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. PROPOSAL                                                    │
│     └── Anyone can propose via GitHub Discussion or Issue      │
│                                                                 │
│  2. DISCUSSION                                                  │
│     └── Open discussion for community feedback (min 3 days)    │
│                                                                 │
│  3. FEEDBACK                                                    │
│     └── Address concerns, iterate on proposal                   │
│                                                                 │
│  4. DECISION                                                    │
│     └── Based on decision type:                                │
│         • Trivial: Single maintainer approval                  │
│         • Minor: 2+ maintainer approvals                       │
│         • Major: Community vote (50%+1 majority)               │
│         • Strategic: Steering Committee vote (2/3 majority)    │
│                                                                 │
│  5. IMPLEMENTATION                                              │
│     └── Execute with community oversight                        │
│                                                                 │
│  6. REVIEW                                                      │
│     └── Evaluate outcome, document lessons                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Voting Process

#### Who Can Vote

| Decision Level | Voters |
|----------------|--------|
| Minor | Maintainers |
| Major | All contributors with 3+ merged PRs |
| Strategic | Steering Committee members |

#### How to Vote

1. **GitHub Reactions** on proposals
   - 👍 Yes / Approve
   - 👎 No / Reject
   - 🚀 Strong support
   - 👀 Abstain / Watching

2. **Comment** your detailed position

3. **Voting Period:**
   - Minor decisions: 3 days
   - Major decisions: 7 days
   - Strategic decisions: 14 days

#### Vote Counting

- **Majority:** Simple majority (>50%)
- **Quorum:** Minimum 3 votes for minor, 5 for major
- **Tie-breaking:** Steering Committee Chair

### Appeals Process

If you disagree with a decision:

1. **Request Clarification** - Ask for rationale
2. **Submit Appeal** - Create a new discussion explaining concerns
3. **Reconsideration** - Steering Committee reviews within 14 days
4. **Final Decision** - Steering Committee vote (2/3 to overturn)

---

## Maintainer Roles

### Role Hierarchy

```
┌─────────────────────────────────────────┐
│     STEERING COMMITTEE                  │
│  (Project vision & strategic decisions) │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│     LEAD MAINTAINERS                    │
│  (Technical direction & releases)       │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│     CORE MAINTAINERS                    │
│  (Code review & issue triage)           │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│     CONTRIBUTOR COMMUNITY               │
│  (Contributions & feedback)             │
└─────────────────────────────────────────┘
```

### Steering Committee

**Responsibilities:**
- Set project vision and direction
- Make strategic decisions
- Resolve conflicts and appeals
- Approve major architectural changes
- Manage project resources

**Membership:**
- Chair: @SHAdd0WTAka (Project Founder)
- Minimum 3 members, maximum 7
- Members serve 1-year terms
- Re-elected by majority vote

**Current Members:**
| Member | Role | Since |
|--------|------|-------|
| @SHAdd0WTAka | Chair, Project Founder | 2024 |
| *Open Position* | Community Representative | - |
| *Open Position* | Technical Lead | - |

### Lead Maintainers

**Responsibilities:**
- Technical leadership in specific areas
- Review and merge PRs
- Plan releases
- Mentor contributors

**Requirements:**
- 25+ merged PRs
- Deep expertise in project area
- Demonstrated leadership
- Commitment to 5+ hours/week

**Areas:**
| Area | Lead | Backup |
|------|------|--------|
| Core Framework | @SHAdd0WTAka | TBD |
| Web UI | TBD | TBD |
| Security | TBD | TBD |
| DevOps/CI/CD | TBD | TBD |

### Core Maintainers

**Responsibilities:**
- Triage issues
- Review PRs
- Support community
- Maintain documentation

**Requirements:**
- 10+ merged PRs
- Active for 3+ months
- Good communication skills

**Current Core Maintainers:**
- @SHAdd0WTAka
- *Positions open - apply via GitHub Discussion!*

### Becoming a Maintainer

```
┌─────────────────────────────────────────┐
│  PATH TO MAINTAINERSHIP                 │
├─────────────────────────────────────────┤
│                                         │
│  1. CONTRIBUTOR                         │
│     └── Make contributions             │
│                                         │
│  2. ACTIVE CONTRIBUTOR (10+ PRs)        │
│     └── Consistent quality work        │
│                                         │
│  3. NOMINATION                          │
│     └── Existing maintainer nominates  │
│                                         │
│  4. COMMUNITY FEEDBACK                  │
│     └── 7-day discussion period        │
│                                         │
│  5. VOTE                                │
│     └── Maintainers vote (majority)    │
│                                         │
│  6. PROBATION                           │
│     └── 3-month trial period           │
│                                         │
│  7. FULL MAINTAINER                     │
│     └── Official appointment           │
│                                         │
└─────────────────────────────────────────┘
```

### Maintainer Expectations

| Expectation | Frequency | Notes |
|-------------|-----------|-------|
| Code review | Weekly | Review assigned PRs |
| Issue triage | Weekly | Respond to new issues |
| Community engagement | Monthly | Attend community calls |
| Documentation updates | As needed | Keep docs current |
| Security response | Within 24h | Critical security issues |

### Stepping Down

Maintainers can step down at any time:
1. Notify Steering Committee
2. Transition responsibilities
3. Remain recognized as Emeritus Maintainer

---

## Contribution Tiers

### Tier System

We recognize contributors through a tiered system based on contribution quality and quantity.

#### Tier 1: Explorer 🌱
*First steps into the community*

**Requirements:**
- First contribution merged

**Recognition:**
- Listed in CONTRIBUTORS.md
- Discord "Explorer" role
- Welcome package (digital badge)

#### Tier 2: Builder 🔧
*Regular contributor*

**Requirements:**
- 5+ merged PRs OR
- Significant documentation contribution OR
- 3+ substantial bug reports

**Recognition:**
- Listed in CONTRIBUTORS.md with contributions
- Discord "Builder" role
- Monthly contributor shoutout

#### Tier 3: Architect 🏗️
*Major contributor*

**Requirements:**
- 15+ merged PRs OR
- Implemented major feature OR
- Significant community impact

**Recognition:**
- Featured in release notes
- Discord "Architect" role
- Input on feature prioritization
- Early access to new features

#### Tier 4: Guardian 🛡️
*Exceptional contributor*

**Requirements:**
- 30+ merged PRs OR
- Sustained contribution over 6+ months OR
- Major architectural contribution

**Recognition:**
- Hall of Fame induction
- Discord "Guardian" role
- Vote on major decisions
- Invitation to maintainer track

#### Tier 5: Luminary ⭐
*Community leader*

**Requirements:**
- Steering Committee member OR
- 50+ merged PRs with exceptional quality OR
- Sustained leadership over 1+ year

**Recognition:**
- Permanent Hall of Fame
- All Guardian benefits
- Steering Committee voting rights
- Conference speaking opportunities

### Contribution Types

All contributions count towards tier progression:

| Type | Weight | Examples |
|------|--------|----------|
| Code | 1.0x | PRs, bug fixes, features |
| Documentation | 0.8x | Docs, tutorials, translations |
| Bug Reports | 0.5x | Detailed bug reports |
| Community | 0.5x | Helping others, mentoring |
| Design | 0.8x | UI/UX, graphics |
| Testing | 0.7x | Test cases, QA |
| Security | 1.5x | Vulnerability reports |
| Content | 0.6x | Blog posts, videos |

### Tracking Progress

Contributors can track their progress via:
- [CONTRIBUTORS.md](../CONTRIBUTORS.md) - Public recognition
- GitHub profile - Contribution graph
- Discord bot - Automated tier tracking

### Tier Review

Tiers are reviewed:
- **Quarterly:** Automatic tier assignment based on metrics
- **Annually:** Full review of exceptional cases
- **On-request:** For disputes or special circumstances

---

## Project Governance Evolution

### Change Process

This governance document can be updated through:

1. **Proposal:** Create a GitHub Discussion with `governance` label
2. **Community Input:** 14-day discussion period
3. **Steering Committee Review:** Evaluate and refine
4. **Vote:** 2/3 majority of Steering Committee
5. **Implementation:** Update documentation
6. **Announcement:** Notify community of changes

### Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | Feb 2026 | Initial governance document | @SHAdd0WTAka |

---

## Conflict Resolution

### Types of Conflicts

| Type | Example | Resolution Path |
|------|---------|-----------------|
| Technical | Design disagreements | Technical discussion, maintainer vote |
| Personal | Personality clashes | Mediation, Code of Conduct enforcement |
| Resource | Competing priorities | Steering Committee decision |
| Strategic | Direction disputes | Community vote |

### Resolution Steps

1. **Direct Discussion** - Parties discuss directly
2. **Mediation** - Neutral third party facilitates
3. **Escalation** - Steering Committee介入
4. **Final Decision** - Steering Committee vote

### Code of Conduct Enforcement

See [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md) for:
- Reporting procedures
- Investigation process
- Enforcement actions
- Appeals process

---

## Resources & References

- [Code of Conduct](../CODE_OF_CONDUCT.md)
- [Contributing Guide](../CONTRIBUTING.md)
- [Community Guide](COMMUNITY.md)
- [Roadmap](ROADMAP.md)

---

## Questions?

For governance questions or suggestions:
- 💬 [Start a Discussion](https://github.com/SHAdd0WTAka/zen-ai-pentest/discussions/categories/governance)
- 📧 Email: governance@zen-ai-pentest.dev

---

*Last Updated: February 2026*
*Next Review: August 2026*
