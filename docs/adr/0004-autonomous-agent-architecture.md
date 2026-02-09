# ADR 0004: Autonomous Agent Architecture (2026)

## Status
Proposed

## Context
Current system requires significant human oversight. To compete with top-tier tools (Penligent, AutoPentest), we need true autonomy.

## Decision
Implement a fully autonomous agentic workflow using ReAct/Plan-and-Execute pattern.

## Architecture

### High-Level Flow
```
Goal → Planner → Executor → Observer → Validator → [Loop until goal achieved]
```

### Components

#### 1. Goal Parser
Decomposes high-level goals into sub-tasks.
```python
class GoalParser:
    def parse(self, goal: str) -> List[Task]:
        # "Find RCE in API" → [
        #   Task(recon),
        #   Task(identify_vulns),
        #   Task(validate_exploit),
        #   Task(report)
        # ]
```

#### 2. ReAct Loop
```python
while not done:
    thought = llm.reason(context)
    action = select_tool(thought)
    observation = execute(action)
    memory.store(thought, action, observation)
    done = validate_goal()
```

#### 3. Tool Registry
Dynamic tool discovery and execution.
```python
@tool("nmap", category="recon")
async def nmap_scan(target: str, ports: str = "top-100") -> ScanResult:
    ...
```

#### 4. Memory Layers
- Working: Current session
- Short-term: Last N actions
- Long-term: Vector store of findings
- Episodic: Full attack chains

## Consequences

### Positive
- True autonomy
- Scalable to complex targets
- Learning from past operations

### Negative
- Increased complexity
- Debugging difficulty
- Potential for unexpected behavior
- Safety concerns

## Safety Measures
1. Human approval gates for destructive actions
2. Sandbox execution
3. Timeout limits
4. Rollback capability

## References
- [ReAct Paper](https://arxiv.org/abs/2210.03629)
- [LangGraph](https://python.langchain.com/docs/langgraph)
- [CrewAI](https://github.com/joaomdmoura/crewAI)
