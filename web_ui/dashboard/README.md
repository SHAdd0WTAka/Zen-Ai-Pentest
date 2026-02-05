# Zen AI Pentest Dashboard

Modern React-based Web UI Dashboard for Issue #24 - Real-time penetration testing management interface.

## Features

- **📊 Real-time Dashboard**: Live statistics, charts, and activity feeds
- **🔍 Scan Management**: Create, monitor, and control security scans
- **🛡️ Findings Management**: Review, verify, and export security findings
- **🤖 Agent Monitor**: Real-time agent activity and thought process streaming
- **⚡ WebSocket Integration**: Live updates without page refresh
- **📱 Responsive Design**: Works on desktop and mobile devices

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Project Structure

```
web_ui/dashboard/
├── src/
│   ├── components/
│   │   ├── Dashboard.tsx       # Main dashboard with stats & charts
│   │   ├── ScanManager.tsx     # Scan creation & management
│   │   ├── FindingsList.tsx    # Findings review & verification
│   │   └── AgentMonitor.tsx    # Real-time agent monitoring
│   ├── App.tsx                 # Main app with routing
│   ├── main.tsx                # Entry point
│   ├── index.css               # Global styles
│   └── vite-env.d.ts           # TypeScript declarations
├── public/
│   └── index.html              # HTML template
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## API Integration

The dashboard integrates with the following API endpoints:

### Dashboard API
- `GET /api/v1/dashboard/stats` - Dashboard statistics
- `GET /api/v1/dashboard/active-scans` - Active scan list
- `GET /api/v1/dashboard/recent-findings` - Recent findings
- `WS /api/v1/dashboard/ws` - Real-time updates

### Scan API
- `POST /api/v1/scans/` - Create new scan
- `GET /api/v1/scans/{id}/status` - Scan status
- `GET /api/v1/scans/{id}/logs` - Scan logs
- `WS /api/v1/scans/{id}/ws` - Real-time scan updates

### Agent API
- `GET /api/v1/agents/active` - List active agents
- `GET /api/v1/agents/{id}/info` - Agent details
- `GET /api/v1/agents/{id}/thoughts` - Agent thoughts
- `WS /api/v1/agents/{id}` - Real-time agent monitoring
- `WS /api/v1/agents/ws/global` - Global agent updates

## Technology Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **WebSocket**: Native WebSocket API
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **State Management**: React hooks + Zustand (ready)
- **Notifications**: React Hot Toast

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Development

```bash
# Run type checker
npm run type-check

# Run linter
npm run lint

# Preview production build
npm run preview
```

## License

Part of the Zen AI Pentest Framework
