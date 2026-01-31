# Zen AI Pentest - Web UI Frontend

React-based frontend for the Zen AI Pentest framework.

## Features

- **Real-time Scan Monitoring**: WebSocket-based live updates
- **Agent Status Dashboard**: Monitor autonomous agent progress
- **Risk Score Visualization**: Interactive risk scoring display
- **Findings Management**: Filter and prioritize security findings

## Installation

```bash
npm install
```

## Development

```bash
npm start
```

Open http://localhost:3000

## Build

```bash
npm run build
```

## Components

| Component | Description |
|-----------|-------------|
| `ScanDashboard` | Active scans overview with progress |
| `AgentStatus` | Real-time agent monitoring |
| `FindingsList` | Security findings with filtering |
| `RiskScoreCard` | Risk score visualization |

## API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000`.

### WebSocket Endpoints
- `/ws/scans` - Scan updates
- `/ws/agents` - Agent status updates

### REST Endpoints
- `GET /api/scans` - List scans
- `POST /api/scan` - Start new scan
- `GET /api/findings` - List findings
- `GET /api/agents` - List agents
