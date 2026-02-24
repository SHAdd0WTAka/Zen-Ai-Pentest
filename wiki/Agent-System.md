# Agent System

Zen-AI-Pentest nutzt ein Multi-Agent-System für autonome Penetrationstests.

## Agent-Typen

### 1. Recon Agent
**Aufgabe:** Information Gathering
- Subdomain Enumeration
- Port Scanning
- Technologie-Erkennung

**CLI:**
```bash
python3 -m agents.cli recon --target example.com
```

### 2. Exploit Agent
**Aufgabe:** Schwachstellen-Exploitation
- Automatische Exploit-Auswahl
- Sichere Sandbox-Ausführung
- Evidence Collection

**CLI:**
```bash
python3 -m agents.cli exploit --target example.com --vulnerability CVE-2021-44228
```

### 3. Analysis Agent
**Aufgabe:** Ergebnis-Analyse
- False-Positive Detection
- Risiko-Bewertung
- Report-Generierung

### 4. ReAct Agent
**Aufgabe:** Autonome Entscheidungsfindung
- Reason → Act → Observe → Reflect
- Selbstständige Planung
- Adaptive Strategien

## ReAct Pattern

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Reason  │───▶│   Act   │───▶│ Observe │───▶│ Reflect │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
     ▲                                            │
     └────────────────────────────────────────────┘
```

**Beispiel:**
```python
from agents.react_agent import ReActAgent

agent = ReActAgent(
    persona="security_analyst",
    tools=["nmap", "nuclei", "sqlmap"]
)

result = await agent.run(
    task="Scan example.com for vulnerabilities"
)
```

## State Machine

```
IDLE → PLANNING → EXECUTING → OBSERVING → REFLECTING → COMPLETED
              │         │           │            │
              └─────────┴───────────┴────────────┘
                         (Retry Loop)
```

## Risk Levels

| Level | Beschreibung | Aktion |
|-------|--------------|--------|
| 0 | Info | Automatisch |
| 1 | Low | Automatisch |
| 2 | Medium | Bestätigung nötig |
| 3 | High | Nur mit --force |

## Guardrails

Sicherheits-Kontrollen für alle Agents:

- **Private IP Blocking:** Keine internen Netzwerke
- **Timeout Management:** Max 10 Minuten pro Task
- **Resource Limits:** CPU/Memory Limits
- **Read-Only:** Standardmäßig kein Schreibzugriff

## Agent Koordination

```python
from agents.agent_coordinator_v3 import AgentCoordinator

coordinator = AgentCoordinator()

# Workflow erstellen
workflow = coordinator.create_workflow(
    target="example.com",
    phases=["recon", "scan", "exploit", "report"]
)

# Ausführen
results = await coordinator.execute_workflow(workflow)
```

## CLI Tools

| Command | Beschreibung |
|---------|--------------|
| `k-recon` | Reconnaissance Agent |
| `k-exploit` | Exploitation Agent |
| `k-analyze` | Analysis Agent |
| `k-report` | Report Agent |
| `k-audit` | Audit Agent |
| `k-social` | Social Engineering Agent |
| `k-network` | Network Agent |
| `k-mobile` | Mobile Agent |
| `k-redteam` | Red Team Agent |
| `k-ics` | ICS/SCADA Agent |
| `k-cloud` | Cloud Agent |
| `k-crypto` | Cryptography Agent |

## Beispiel: Kompletter Scan

```bash
# 1. Recon
k-recon --target example.com --output recon.json

# 2. Scan mit gefundenen Subdomains
k-exploit --target-file recon.json --vulnerability-scan

# 3. Report generieren
k-report --scan-id 123 --format pdf
```

## Memory System

- **Short-term:** Aktueller Kontext
- **Long-term:** Gelernte Erkenntnisse
- **Context Window:** Chat-Verlauf

## Troubleshooting

### Agent hängt

```python
# Timeout reduzieren
agent = ReActAgent(timeout=300)  # 5 Minuten
```

### Zu viele False Positives

```python
# Strengere Filter
agent.false_positive_threshold = 0.8
```

### Memory voll

```bash
# Cache leeren
rm -rf ~/.cache/zen-ai-pentest/
```
