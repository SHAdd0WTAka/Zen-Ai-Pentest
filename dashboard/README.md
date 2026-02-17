# Zen-AI Pentest Dashboard

> Modern React Dashboard for Zen-AI Pentest Framework

---

## 🚀 Features

- 📊 **Real-time Dashboard** - Live scan statistics and charts
- 🔍 **Scan Management** - Create, monitor, and view scans
- 🛠️ **Tools Overview** - View all available security tools
- 📈 **Reports** - Generate and download PDF/JSON/HTML reports
- ⚙️ **Settings** - User profile, security, and API keys
- 🔔 **WebSocket Support** - Real-time updates
- 🎨 **Modern UI** - Built with Tailwind CSS

---

## 📦 Tech Stack

- **React 18** + TypeScript
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Zustand** - State management
- **React Query** - API caching
- **Recharts** - Charts
- **Socket.io** - Real-time updates
- **Lucide React** - Icons

---

## 🛠️ Installation

```bash
cd dashboard
npm install
```

---

## 🚀 Development

```bash
# Start dev server
npm run dev

# Dashboard will be at http://localhost:5173
```

---

## 🏗️ Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

---

## 📁 Project Structure

```
dashboard/
├── src/
│   ├── components/      # Reusable components
│   ├── pages/          # Page components
│   ├── store/          # Zustand stores
│   ├── hooks/          # Custom hooks
│   ├── services/       # API services
│   ├── types/          # TypeScript types
│   └── utils/          # Utilities
├── public/             # Static files
└── package.json
```

---

## 🔌 API Integration

The dashboard connects to the FastAPI backend:
- Default API URL: `http://localhost:8000`
- WebSocket: `ws://localhost:8000/ws`

Configured in `vite.config.ts` with proxy settings.

---

## 🎨 UI Components

### Buttons
```tsx
<button className="btn-primary">Primary</button>
<button className="btn-secondary">Secondary</button>
<button className="btn-danger">Danger</button>
```

### Cards
```tsx
<div className="card">
  <h3>Title</h3>
  <p>Content</p>
</div>
```

### Badges
```tsx
<span className="badge-success">Success</span>
<span className="badge-danger">Danger</span>
<span className="badge-warning">Warning</span>
```

---

## 📄 Pages

| Page | Route | Description |
|------|-------|-------------|
| Login | `/login` | Authentication |
| Dashboard | `/` | Overview & stats |
| Scans | `/scans` | Scan list |
| New Scan | `/scans/new` | Create scan |
| Scan Details | `/scans/:id` | View scan results |
| Tools | `/tools` | Tool inventory |
| Reports | `/reports` | Generate reports |
| Settings | `/settings` | User settings |

---

## 🔐 Authentication

Uses JWT tokens stored in localStorage via Zustand persist middleware.

---

**Built with ❤️ for security professionals**
