# ReAct Agent für Zen-AI-Pentest

## Übersicht

Der **ReAct Agent** implementiert ein autonomes Reasoning-Acting-Observing-Reflecting Pattern für Zen-AI-Pentest. Er nutzt **LangGraph** für den stateful Agent-Loop.

## Architektur

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   START     │────▶│  Agent Node  │────▶│ Conditional │
└─────────────┘     │  (Reason)    │     │   Edge      │
                    └──────────────┘     └──────┬──────┘
                           ▲                    │
                           │         ┌──────────┴──────────┐
                           │         │                     │
                    ┌──────┴──────┐  │  Tool Calls?        │
                    │  Tools Node │◀─┘                     │
                    │   (Act)     │◀───────────────────────┘
                    └─────────────┘    (Yes: Tools, No: End)
```

## Komponenten

### 1. AgentState

Der State persistiert über Iterationen:

```python
class AgentState(TypedDict):
    messages: List[BaseMessage]      # Chat-History
    findings: List[dict]             # Pentest-Ergebnisse
    target: str                      # Aktuelles Ziel
    iteration: int                   # Loop-Counter
    max_iterations: int              # Safety-Limit
    status: Literal["running", "paused", "completed", "error"]
```

### 2. Nodes

#### Agent Node (Reason/Plan)
- Entscheidet nächsten Schritt
- Ruft LLM mit Tool-Binding auf
- Checkt Iterations-Limit

#### Tools Node (Act/Observe)
- Führt Tools aus (sandboxed)
- Sammelt Ergebnisse
- Speichert Findings

### 3. Tools

| Tool | Zweck | Dangerous? |
|------|-------|------------|
| `scan_ports` | Nmap Port Scan | Nein |
| `scan_vulnerabilities` | Nuclei CVE Scan | Nein |
| `enumerate_directories` | ffuf Dir Brute | Nein |
| `lookup_cve` | CVE DB Lookup | Nein |
| `validate_exploit` | Exploit Validation | **Ja** |

### 4. Security Features

- **Sandboxing**: Alle Tools in Docker-Containern
- **Human-in-the-Loop**: Pausiert bei gefährlichen Aktionen
- **Auto-Approve**: Konfigurierbar für automatische Ausführung
- **Iterations-Limit**: Verhindert Infinite Loops

## Verwendung

### Basis-Beispiel

```python
from agents.react_agent import ReActAgent, ReActAgentConfig

# Konfiguration
config = ReActAgentConfig(
    max_iterations=10,
    enable_sandbox=True,
    auto_approve_dangerous=False
)

# Agent erstellen
agent = ReActAgent(config)

# Scan ausführen
result = agent.run(
    target="example.com",
    objective="Port scan and vulnerability assessment"
)

# Report generieren
print(agent.generate_report(result))
```

### Mit Human-in-the-Loop

```python
config = ReActAgentConfig(
    use_human_in_the_loop=True,
    auto_approve_dangerous=False  # Manuelle Freigabe
)

agent = ReActAgent(config)
result = agent.run("target.com", "Full penetration test")
```

### Continuous Monitoring

```python
import schedule
import time

config = ReActAgentConfig(max_iterations=5)
agent = ReActAgent(config)

def daily_scan():
    result = agent.run("target.com", "Quick check")
    # Speichere Ergebnisse...

schedule.every().day.at("02:00").do(daily_scan)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## Konfiguration

### ReActAgentConfig

| Parameter | Default | Beschreibung |
|-----------|---------|--------------|
| `max_iterations` | 10 | Maximale Loop-Iterationen |
| `enable_sandbox` | True | Docker-Sandbox aktivieren |
| `auto_approve_dangerous` | False | Auto-Freigabe für Exploits |
| `use_human_in_the_loop` | True | Pausiert bei gefährlichen Aktionen |
| `llm_model` | "gpt-4o" | LLM-Modell |

## Integration in Zen-AI-Pentest

### In orchestrator.py

```python
from agents.react_agent import get_agent

class PentestOrchestrator:
    def __init__(self):
        self.react_agent = get_agent()
    
    def run_autonomous_scan(self, target, objective):
        return self.react_agent.run(target, objective)
```

### In CLI

```bash
# Autonomer Scan
python -m zen_ai_pentest scan --target example.com --mode autonomous

# Mit Human-in-the-Loop
python -m zen_ai_pentest scan --target example.com --mode interactive
```

## Tests

```bash
# Alle Tests ausführen
pytest tests/test_react_agent.py -v

# Spezifische Test-Kategorie
pytest tests/test_react_agent.py::TestReActAgentSecurity -v
```

## Fehlerbehebung

### Problem: Agent looped unendlich
**Lösung**: `max_iterations` prüfen, Conditions in `should_continue` debuggen

### Problem: Tools werden nicht aufgerufen
**Lösung**: LLM Tool-Binding prüfen, Prompt-Engineering verbessern

### Problem: Sandbox nicht verfügbar
**Lösung**: Docker installieren/starten, `enable_sandbox=False` für Tests

### Problem: Gefährliche Aktionen blockiert
**Lösung**: `auto_approve_dangerous=True` (nur für autorisierte Tests!)

## Roadmap-Integration

Diese Implementierung deckt ab:

- ✅ **2026 Q1**: ReAct / Plan-and-Execute Reasoning Loop
- ✅ **2026 Q1**: Real Tool Calling Framework
- ✅ **2026 Q1**: Memory System mit LangGraph
- 🔄 **2026 Q2**: False-Positive Reduction (mit EPSS/CVSS)
- 🔄 **2026 Q2**: Hallucination Protection

## Ressourcen

- [LangGraph Dokumentation](https://langchain-ai.github.io/langgraph/)
- [ReAct Paper](https://arxiv.org/abs/2210.03629)
- [Zen-AI-Pentest Roadmap](../ROADMAP.md)
