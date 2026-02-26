# Zen-AI-Pentest System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  ZEN-AI-PENTEST v2.2 - Modular Security Framework          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   React     │    │    CLI      │    │   REST API  │     │
│  │  Dashboard  │◄──►│  (Typer)    │◄──►│  (FastAPI)  │     │
│  └─────────────┘    └─────────────┘    └──────┬──────┘     │
│                                               │             │
│  ┌────────────────────────────────────────────┼─────────┐   │
│  │              CORE ORCHESTRATOR             │         │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐   │         │   │
│  │  │  ReAct   │ │  Risk    │ │ Subdomain│   │         │   │
│  │  │  Agent   │ │  Engine  │ │ Scanner  │   │         │   │
│  │  └──────────┘ └──────────┘ └──────────┘   │         │   │
│  └────────────────────────────────────────────┼─────────┘   │
│                                               │             │
│  ┌────────────────────────────────────────────┘             │
│  │                    TOOLS LAYER                           │
│  │  Network: Nmap │ Masscan    Web: SQLMap │ Nuclei        │
│  │  Exploit: Metasploit       Recon: Amass │ TheHarvester  │
│  └─────────────────────────────────────────────────────────┘
│                                                             │
│  Data: PostgreSQL │ Redis │ Evidence Store │ Report Gen    │
└─────────────────────────────────────────────────────────────┘
```

## Component Overview

| Layer | Components | Purpose |
|-------|-----------|---------|
| **UI** | React Dashboard, CLI, REST API | User interaction |
| **Core** | ReAct Agent, Risk Engine, Subdomain Scanner | Intelligence |
| **Tools** | 72+ integrated security tools | Execution |
| **Data** | PostgreSQL, Redis, Evidence Store | Persistence |

## Key Features

- **Autonomous**: ReAct pattern with memory
- **Safe**: Sandboxed exploit validation
- **Integrated**: Subdomain enumeration, CVE tracking
- **Extensible**: Plugin architecture
