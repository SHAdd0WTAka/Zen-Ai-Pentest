# Zen AI Pentest Architecture

## System Architecture Diagram

```mermaid
graph TB
    subgraph "User Interface Layer"
        CLI[CLI Interface]
        API[REST API / FastAPI]
        WebUI[React Web UI]
    end

    subgraph "Core Engine"
        Orchestrator[Agent Orchestrator]
        StateMachine[State Machine<br/>IDLE → PLANNING → EXECUTING → OBSERVING]
        Memory[Memory System<br/>Short-term / Long-term]
        RiskEngine[Risk Engine<br/>Scoring & Validation]
    end

    subgraph "AI Agents"
        ReconAgent[Reconnaissance Agent]
        VulnAgent[Vulnerability Agent]
        ExploitAgent[Exploit Agent]
        ReportAgent[Report Agent]
        Consensus[LLM Voting Consensus]
    end

    subgraph "Tool Integration"
        Nmap[Nmap]
        Gobuster[Gobuster]
        SQLMap[SQLMap]
        Metasploit[Metasploit]
        CustomTools[Custom Tools]
    end

    subgraph "Data Storage"
        Evidence[Evidence Collection]
        Logs[Audit Logs]
        Reports[Generated Reports]
        CVE_DB[CVE Database]
    end

    subgraph "External APIs"
        OpenAI[OpenAI API]
        Anthropic[Anthropic API]
        Ollama[Local Ollama]
        ThreatIntel[Threat Intelligence<br/>ThreatFox / URLhaus]
    end

    CLI --> API
    WebUI --> API
    API --> Orchestrator
    
    Orchestrator --> StateMachine
    Orchestrator --> Memory
    Orchestrator --> RiskEngine
    
    StateMachine --> ReconAgent
    StateMachine --> VulnAgent
    StateMachine --> ExploitAgent
    StateMachine --> ReportAgent
    
    ReconAgent --> Nmap
    ReconAgent --> Gobuster
    VulnAgent --> SQLMap
    ExploitAgent --> Metasploit
    
    ReconAgent --> Consensus
    VulnAgent --> Consensus
    ExploitAgent --> Consensus
    
    Consensus --> OpenAI
    Consensus --> Anthropic
    Consensus --> Ollama
    
    RiskEngine --> ThreatIntel
    RiskEngine --> CVE_DB
    
    ExploitAgent --> Evidence
    ReportAgent --> Reports
    Orchestrator --> Logs
```

## Component Overview

### 1. User Interface Layer
- **CLI**: Command-line interface for scripting and automation
- **REST API**: FastAPI-based backend for web integration
- **Web UI**: React-based dashboard for interactive use

### 2. Core Engine
- **Agent Orchestrator**: Manages multi-agent workflow and task distribution
- **State Machine**: Implements ReAct pattern (Reason → Act → Observe → Reflect)
- **Memory System**: Maintains context across sessions
- **Risk Engine**: Validates findings and calculates risk scores

### 3. AI Agents
Specialized agents for different penetration testing phases:
- **Reconnaissance**: Network scanning and enumeration
- **Vulnerability**: Identifies security weaknesses
- **Exploit**: Attempts controlled exploitation
- **Report**: Generates comprehensive reports

### 4. Tool Integration
Integrates with industry-standard security tools:
- Nmap, Gobuster, SQLMap, Metasploit
- Custom exploitation modules

### 5. External APIs
- **LLM Providers**: OpenAI, Anthropic, Local Ollama
- **Threat Intelligence**: Real-time threat data

## Data Flow

1. User input → API → Orchestrator
2. Orchestrator selects appropriate agent
3. Agent uses tools and AI consensus
4. Results validated by Risk Engine
5. Evidence collected and reports generated
