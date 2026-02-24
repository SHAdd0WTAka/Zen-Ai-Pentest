# Hierarchische Agent-Architektur (Security by Design)

> **Prinzip**: Das Haupt-LLM kennt das volle Bild, Worker-Agenten nur ihre spezifische Aufgabe

## 🏗️ Architektur-Übersicht

```
┌─────────────────────────────────────────────────────────────────┐
│                     KIMI (Haupt-Agent)                          │
│                     ═══════════════════                          │
│  • Kennt das komplette Ziel                                     │
│  • Plant die Strategie                                          │
│  • Koordiniert Worker                                           │
│  • Enforced Safety Level 3-4 (kritische Entscheidungen)         │
└────────────────────────┬────────────────────────────────────────┘
                         │ Delegation
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              CORE AGENTS (Open-Source LLMs)                     │
│              ═══════════════════════════════                     │
│  • Mistral / Llama / DeepSeek (lokal oder API)                  │
│  • Safety Level 1-2 nur (moderate Aufgaben)                     │
│  • Kein Kontext über Gesamtziel                                 │
│  • Strikte Template-basierte Aufgaben                           │
└────────────────────────┬────────────────────────────────────────┘
                         │ Ausführung
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SUB-AGENTS (Tools)                           │
│                    ═══════════════════                           │
│  • Nmap, SQLMap, etc. (kein LLM, nur Tool)                      │
│  • Direkte Ausführung                                           │
│  • Ergebnisse → Datenbank                                       │
└─────────────────────────────────────────────────────────────────┘
```

## 🔒 Sicherheitskonzept: "Compartmentalisierung"

### 1. Das "Vollbild"-Prinzip

| Ebene | Kennt Ziel | Safety Level | Aufgabe |
|-------|-----------|--------------|---------|
| **Kimi (Haupt)** | ✅ Komplett | 3-4 | Strategie, Kritische Entscheidungen |
| **Core Agents** | ❌ Nur Teilaufgabe | 1-2 | Ausführung, Daten sammeln |
| **Sub-Agenten** | ❌ Gar nichts | N/A | Tool-Ausführung |

### 2. Template-basierte Delegation

Statt: "Scanne das Ziel und entscheide was zu tun ist"

Template für Worker:
```yaml
task_template:
  agent_role: "Port Scanner"
  input_format:
    target_ip: "string"
    port_range: "string"
  output_format:
    open_ports: "list"
    service_versions: "dict"
  restrictions:
    - "NO_DECISION_MAKING"
    - "NO_ESCALATION"
    - "ONLY_RETURN_RAW_DATA"
  safety_level: 1  # Read-only, keine Exploits
```

### 3. Die "2-Fliegen-mit-einer-Klappe"-Lösung

**Problem 1**: Worker-LLMs verweigern Aufgaben (Moral, Sicherheit)
**Problem 2**: Kosten für API-Calls
**Problem 3**: Chain of Custody Lücken

**Lösung**:
```
┌─────────────────────────────────────────────────────────────┐
│  WORKER-LLM (z.B. Mistral 7B lokal)                         │
│                                                             │
│  Input:  Striktes Template + konkrete Daten                 │
│  ─────────────────────────────────────────                  │
│  "Analysiere diesen Nmap-Output:                           │
│   - Liste offene Ports                                      │
│   - Identifiziere Service-Versionen                         │
│   - KEINE Handlungsempfehlungen                             │
│   - KEINE ethischen Bewertungen"                            │
│                                                             │
│  Output: Strukturierte Daten (JSON)                         │
│  ─────────────────────────────────                          │
│  {                                                          │
│    "open_ports": [80, 443],                                 │
│    "services": {                                            │
│      "80": "Apache 2.4.41",                                 │
│      "443": "Nginx 1.18.0"                                  │
│    }                                                        │
│  }                                                          │
│                                                             │
│  → Direkt in PostgreSQL geschrieben                         │
│  → Kimi liest und entscheidet nächsten Schritt              │
└─────────────────────────────────────────────────────────────┘
```

## 💰 Kosten-Optimierung

| Aufgabe | Vorher (GPT-4) | Nachher (Mistral lokal) | Ersparnis |
|---------|---------------|------------------------|-----------|
| Port-Scan Analyse | $0.02 | $0 (lokal) | 100% |
| SQLi Detection | $0.05 | $0 (lokal) | 100% |
| Report Generation | $0.10 | $0.02 (Kimi) | 80% |
| Strategie-Planung | $0.20 | $0.10 (Kimi) | 50% |

**Gesamt**: ~90% Kostenreduktion durch lokale Worker

## 🔧 Technische Umsetzung

### Worker-LLM Integration

```python
class WorkerAgent:
    """Open-Source LLM für spezifische Aufgaben"""
    
    def __init__(self, model="mistral:7b"):
        self.model = model  # Ollama, llama.cpp, etc.
        self.safety_level = 1  # Max Level 2
        
    async def execute_task(self, template: TaskTemplate, data: dict):
        # Strict prompt engineering
        prompt = f"""
        ROLE: {template.agent_role}
        TASK: {template.description}
        
        INPUT DATA:
        {json.dumps(data, indent=2)}
        
        RULES:
        {chr(10).join(f"- {r}" for r in template.restrictions)}
        
        OUTPUT FORMAT (JSON):
        {json.dumps(template.output_format, indent=2)}
        
        Respond ONLY with valid JSON. No explanations.
        """
        
        # Local inference
        result = await ollama.generate(
            model=self.model,
            prompt=prompt,
            format="json",
            options={
                "temperature": 0.1,  # Deterministisch
                "num_predict": 500,   # Kurze Antworten
            }
        )
        
        # Validate output structure
        return json.loads(result['response'])
```

### Datenfluss & Chain of Custody

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Kimi       │────▶│   Worker     │────▶│  PostgreSQL  │
│  (Orchester) │     │   (Mistral)  │     │  (Audit-DB)  │
└──────────────┘     └──────────────┘     └──────────────┘
      │                     │                     │
      │ "Scan Ports"        │ "Ports: 80,443"    │ Timestamp
      │                     │                     │ User-ID
      │                     │                     │ Task-ID
      ▼                     ▼                     ▼
   Komplettes          Nur Input/           Vollständige
   Zielbild           Output               Audit-Trail
```

**Chain of Custody**: ✅ Intakt
- Kimi delegiert (mit Begründung)
- Worker führt aus (nur Daten, keine Entscheidungen)
- Datenbank loggt alles (Timestamp, User, Task, Result)

## 🛡️ Safety Level Mapping

| Level | Wer darf | Beispiel |
|-------|---------|----------|
| **1** | Worker LLMs | Port-Scanning, Banner-Grabbing |
| **2** | Worker LLMs + Validation | Service-Erkennung, CVE-Lookup |
| **3** | Kimi only | Exploit-Auswahl, Payload-Generierung |
| **4** | Kimi + Human Approval | Aktive Exploitation, Data Exfil |

## ✅ Vorteile dieser Architektur

1. **Kosten**: 90% Ersparnis durch lokale Worker
2. **Kontrolle**: Kimi behält strategische Kontrolle
3. **Speed**: Worker parallelisierbar (lokale GPUs)
4. **Privacy**: Keine sensitiven Daten an externe APIs
5. **Compliance**: Vollständiger Audit-Trail in PostgreSQL
6. **Skalierbar**: Worker = commodity Hardware

## ⚠️ Risiken & Mitigation

| Risiko | Mitigation |
|--------|-----------|
| Worker-LLM halluziniert | Strikt JSON-Schema, Validation |
| Worker überschreitet Aufgabe | Template-Enforcement, Sandbox |
| Lokale Ressourcen knapp | Auto-Scaling auf Cloud-Worker |

---

**Fazit**: Hierarchische Architektur mit "Need to know"-Prinzip löst das Agent-Zero-Sicherheitsproblem und reduziert Kosten drastisch.

[← Zurück zur Roadmap](Changelog)
