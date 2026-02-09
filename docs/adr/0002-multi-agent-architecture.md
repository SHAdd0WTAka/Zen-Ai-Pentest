# ADR 0002: Multi-Agent Architecture

## Status
Accepted

## Context
Initial implementation used a single monolithic agent that handled all tasks (reconnaissance, analysis, exploitation). This led to:
- Complex code with multiple responsibilities
- Difficult to extend with new capabilities
- No specialization possible
- Hard to parallelize work

## Decision
We will implement a multi-agent system inspired by Clawed/Moltbot architecture:

### Agent Types
1. **ResearchBot** - Gathers information, OSINT, reconnaissance
2. **AnalysisBot** - Analyzes findings, vulnerability assessment
3. **ExploitBot** - Generates and validates exploit payloads
4. **Orchestrator** - Coordinates agents, manages workflow

### Communication
- Async message passing via queues
- Shared context object for state
- Event-driven architecture

## Consequences

### Positive
- Clear separation of concerns
- Each agent can be optimized independently
- Easy to add new agent types
- Parallel execution possible
- Better testability

### Negative
- Coordination overhead
- Potential for deadlocks
- More complex debugging
- Need for message serialization

## Alternatives Considered

### Single Agent (Status Quo)
Rejected: Too complex, not scalable

### Microservices
Rejected: Too heavy for CLI tool, deployment complexity

### Simple Function Calls
Rejected: No parallelism, tight coupling

## References
- [Clawed Multi-Agent System](https://example.com/clawed)
- [Moltbot Architecture](https://example.com/moltbot)
