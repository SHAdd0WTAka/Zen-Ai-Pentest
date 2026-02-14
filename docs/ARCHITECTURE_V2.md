# 🛡️ Zen-AI-Pentest Architecture

```
╔══════════════════════════════════════════════════════════════════╗
║           ⚔️ AI-Powered Penetration Testing Framework ⚔️          ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  🖥️  UI Layer         🔌 API Layer         🧠 Core Layer         ║
║  ┌─────────┐         ┌─────────┐          ┌─────────────┐       ║
║  │  React  │◄───────►│ FastAPI │◄────────►│ 🤖 ReAct    │       ║
║  │  Dashboard       │  JWT    │          │    Agent     │       ║
║  │  CLI    │         │  Auth   │          │ ⚖️  Risk     │       ║
║  └─────────┘         └─────────┘          │    Engine    │       ║
║                                           │ 🔍 Subdomain │       ║
║                                           │    Scanner   │       ║
║                                           └─────────────┘        ║
║                                                   │               ║
║  🔧 Tools Layer (20+)                             ▼               ║
║  ┌─────────────────────────────────────────────────────────┐     ║
║  │ 🌐 Nmap │ SQLMap │ Metasploit │ Nuclei │ Gobuster       │     ║
║  │ 🎯 Masscan │ Burp │ BloodHound │ CME │ Amass             │     ║
║  └─────────────────────────────────────────────────────────┘     ║
║                                                                  ║
║  💾 Data: PostgreSQL │ Redis │ 📊 Reports │ 🗂️  Evidence        ║
╚══════════════════════════════════════════════════════════════════╝
```

## 🎯 Key Features

| Feature | Description |
|---------|-------------|
| 🤖 **Autonomous** | ReAct pattern with multi-agent orchestration |
| 🛡️ **Safe** | Sandboxed exploit validation & safety controls |
| 🔍 **Recon** | DNS, subdomain enum, certificate transparency |
| ⚖️ **Risk Engine** | CVSS/EPSS scoring, false positive reduction |
| 📊 **Reporting** | PDF/HTML/JSON with compliance templates |

## 🚀 Quick Start

```bash
# Docker (Recommended)
docker-compose up -d

# Subdomain Scan
python scan_target_subdomains.py

# CLI Mode
python tools/subdomain_enum.py target.com --advanced
```

## 📦 Components

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Frontend  │    │     API     │    │    Core     │
│  React/CLI  │───►│  FastAPI    │───►│  Agents     │
└─────────────┘    └─────────────┘    └─────────────┘
                                              │
┌─────────────┐    ┌─────────────┐           │
│    Tools    │    │    Data     │◄──────────┘
│  20+ Pentest│    │  PostgreSQL │
│   Tools     │    │    Redis    │
└─────────────┘    └─────────────┘
```
