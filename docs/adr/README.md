# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) for the Zen AI Pentest project.

## What is an ADR?

An Architecture Decision Record (ADR) captures an important architectural decision made along with its context and consequences. ADRs help teams:

- Understand why decisions were made
- Onboard new team members
- Avoid revisiting decisions unnecessarily
- Document the evolution of the system

## ADR Index

| Number | Title | Status | Date |
|--------|-------|--------|------|
| [0001](0001-record-architecture-decisions.md) | Record Architecture Decisions | Accepted | 2024-01 |
| [0002](0002-multi-agent-architecture.md) | Multi-Agent Architecture | Accepted | 2024-01 |
| [0003](0003-llm-backend-routing.md) | LLM Backend Routing Strategy | Accepted | 2024-01 |

## Proposed ADRs

| Number | Title | Status |
|--------|-------|--------|
| 0004 | AsyncIO vs Threading | Proposed |
| 0005 | JSON vs SQL for CVE DB | Proposed |
| 0006 | Docker vs Native Deployment | Proposed |
| 0007 | Plugin System Architecture | Proposed |

## ADR Format

We use the [MADR](https://adr.github.io/madr/) (Markdown Any Decision Records) format:

```markdown
# ADR XXXX: Title

## Status
- Proposed
- Accepted
- Deprecated
- Superseded by [ADR-YYYY](adr-yyyy.md)

## Context
What is the issue that we're seeing that is motivating this decision?

## Decision
What is the change that we're proposing or have agreed to implement?

## Consequences
What becomes easier or more difficult to do and any risks introduced by the change?

## Alternatives Considered
What other options were considered and why were they rejected?

## References
Links to related documents, issues, or external resources.
```

## Contributing

When creating a new ADR:

1. Use the next available number
2. Copy the template from existing ADRs
3. Set status to "Proposed"
4. Discuss in team / PR
5. Update status to "Accepted" when merged

## Resources

- [ADR GitHub Organization](https://adr.github.io/)
- [MADR Template](https://adr.github.io/madr/)
- [Documenting Architecture Decisions](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions)
