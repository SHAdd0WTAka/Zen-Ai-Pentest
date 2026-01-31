# Zen-AI-Pentest Dashboard

Ein modernes, interaktives Dashboard für das Zen-AI-Pentest Framework mit Echtzeit-Visualisierungen und fortschrittlicher Bedienoberfläche.

## 🚀 Features

### Dashboard
- **Echtzeit-Scan-Status**: Live-Updates via WebSocket/SSE
- **Statistische Übersichten**: Donut-Charts, Bar-Charts, Area-Charts
- **Timeline**: Pentest-Aktivitäten über die Zeit
- **Alert-Panel**: Kritische Funde und Benachrichtigungen
- **Agent-Status-Übersicht**: Verfügbarkeit und Auslastung

### Attack-Graph Visualisierung
- **Interaktive Graph-Visualisierung**: D3.js-basiert
- **Knotentypen**: Hosts, Services, Vulnerabilities, Credentials, Data
- **Zoom und Pan**: Nahtlose Navigation
- **Node-Details**: Klick für detaillierte Informationen
- **Path-Highlighting**: Exploit-Pfade visualisieren
- **Export**: Als PNG oder SVG

### Evidence Viewer
- **Screenshot-Galerie**: Mit Zoom und Lightbox
- **HTTP-Response-Viewer**: JSON/RAW Ansicht
- **PCAP-Player**: Download und Analyse
- **Video-Player**: Für Screen-Recordings
- **Download-Funktionalität**: Für alle Evidence-Typen

### Findings-Tabelle
- **Sortierung**: Nach Severity, Risk, Priority
- **Filtering**: Nach Status, Type, Confidence
- **Bulk-Actions**: Export, Validate, Mark as FP
- **Inline-Editing**: Für Notizen
- **Risk-Score-Anzeige**: Visuelle Darstellung

### Report-Viewer
- **Markdown-Renderer**: Mit Syntax-Highlighting
- **HTML-Preview**: Mit Print-Support
- **PDF-Viewer**: Eingebettet
- **JSON-Tree-View**: Klappbare Struktur
- **Export-Buttons**: Für alle Formate

## 🛠️ Technologie-Stack

- **React 18+** mit TypeScript
- **TailwindCSS** für Styling
- **Recharts** für Charts
- **D3.js** für Graph-Visualisierung
- **React-Query** für Data-Fetching
- **React-Router** für Navigation
- **Axios** für HTTP-Requests

## 📦 Installation

```bash
# Dependencies installieren
npm install

# Entwicklungsserver starten
npm run dev

# Production-Build
npm run build

# Preview
npm run preview
```

## 🔧 Konfiguration

Erstelle eine `.env` Datei im Root-Verzeichnis:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
```

## 📁 Projektstruktur

```
src/
├── components/
│   ├── Dashboard/
│   │   └── AdvancedDashboard.tsx
│   ├── Visualizations/
│   │   └── AttackGraph.tsx
│   ├── Evidence/
│   │   └── EvidenceViewer.tsx
│   ├── Findings/
│   │   └── FindingsTable.tsx
│   ├── Reports/
│   │   └── ReportViewer.tsx
│   ├── ErrorBoundary.tsx
│   ├── Loading.tsx
│   └── Toast.tsx
├── hooks/
│   ├── useScans.ts
│   ├── useFindings.ts
│   ├── useAgents.ts
│   ├── useAlerts.ts
│   └── useWebSocket.ts
├── services/
│   └── api.ts
├── types/
│   └── index.ts
├── utils/
│   └── formatters.ts
├── App.tsx
├── main.tsx
└── index.css
```

## 🎨 Styling

- **Dark Theme**: Cybersecurity-Look
- **Responsive Design**: Mobile-first
- **Animationen**: Für State-Changes
- **Toast-Notifications**: Für Benachrichtigungen

## 🔐 API-Integration

Das Dashboard kommuniziert mit folgenden API-Endpunkten:

### Scan Management
- `GET /api/v1/scans` - Alle Scans abrufen
- `POST /api/v1/scans` - Neuen Scan erstellen
- `GET /api/v1/scans/:id` - Scan-Details
- `POST /api/v1/scans/:id/start` - Scan starten
- `POST /api/v1/scans/:id/stop` - Scan stoppen

### Finding Management
- `GET /api/v1/findings` - Alle Findings abrufen
- `PATCH /api/v1/findings/:id` - Finding aktualisieren
- `POST /api/v1/findings/bulk-update` - Bulk-Update

### Evidence Management
- `GET /api/v1/evidence/:id` - Evidence abrufen
- `POST /api/v1/findings/:id/evidence` - Evidence hochladen

### Agent Control
- `GET /api/v1/agents` - Alle Agents abrufen
- `POST /api/v1/agents/:id/command` - Befehl senden

### Report Generation
- `GET /api/v1/reports` - Alle Reports abrufen
- `POST /api/v1/reports` - Report generieren

### WebSocket
- `ws://localhost:8000/ws` - Echtzeit-Updates

## 🧪 Testing

```bash
# Tests ausführen
npm run test

# Tests mit UI
npm run test:ui

# Linting
npm run lint

# Linting fixen
npm run lint:fix
```

## 📝 TypeScript-Typen

Alle Komponenten verwenden strikte TypeScript-Typen:

```typescript
// Scan Types
interface Scan {
  id: string;
  name: string;
  target: string;
  status: ScanStatus;
  progress: number;
  // ...
}

// Finding Types
interface Finding {
  id: string;
  title: string;
  severity: SeverityLevel;
  riskScore: number;
  // ...
}
```

## ♿ Accessibility

- ARIA-Labels für alle interaktiven Elemente
- Tastatur-Navigation
- Screen Reader Support
- Farbkontrast nach WCAG 2.1

## 🔄 State Management

Verwendet React Query für:
- Server State Management
- Caching
- Background Refetching
- Optimistic Updates

## 📱 Responsive Breakpoints

- **Mobile**: < 640px
- **Tablet**: 640px - 1024px
- **Desktop**: > 1024px

## 🚀 Deployment

```bash
# Build erstellen
npm run build

# Statische Dateien werden in `dist/` generiert
# Diese können auf jedem Static Host deployed werden
```

## 🤝 Mitwirken

1. Fork erstellen
2. Feature-Branch erstellen
3. Änderungen committen
4. Pull Request erstellen

## 📄 Lizenz

MIT License - siehe LICENSE Datei
