# Getting Started with Zen AI Pentest

## Installation

```bash
pip install zen-ai-pentest
```

## Configuration

Create `.env` file:
```bash
OPENAI_API_KEY=sk-...
ZEN_SAFETY_LEVEL=non_destructive
```

## First Scan

```python
import asyncio
from autonomous.react import ReActLoop, AgentConfig

async def main():
    config = AgentConfig(max_iterations=10)
    agent = ReActLoop(llm_client=client, config=config)
    
    result = await agent.run(
        goal="Find web vulnerabilities",
        target="https://example.com"
    )
    print(result)

asyncio.run(main())
```

## Risk Scoring

```python
from risk_engine import RiskScorer

scorer = RiskScorer()
score = scorer.calculate(
    finding={"cvss_score": 9.8, "cve_id": "CVE-2021-44228"},
    target_context={"internet_facing": True}
)
print(f"Risk: {score.value} ({score.severity.name})")
```

## Web UI

```bash
cd web_ui/backend
uvicorn main:app --reload
```

Access at http://localhost:8000
