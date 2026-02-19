# ☁️ Cloudflare Deployment

Diese Anleitung beschreibt die kostenlose Bereitstellung von Zen-AI-Pentest auf Cloudflare.

## 📋 Voraussetzungen

1. [Cloudflare Account](https://dash.cloudflare.com/sign-up) (kostenlos)
2. [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/install-and-update/)
3. Node.js 20+

## 🚀 Schnellstart

### 1. Wrangler installieren

```bash
npm install -g wrangler
```

### 2. Einloggen

```bash
wrangler login
```

### 3. KV Namespace erstellen

```bash
cd cloudflare
wrangler kv:namespace create CACHE
# Kopiere die ID in wrangler.toml
```

### 4. Secrets setzen

```bash
wrangler secret put JWT_SECRET
wrangler secret put KIMI_API_KEY
```

### 5. Frontend bauen

```bash
cd ../web_ui/frontend
npm install
npm run build
```

### 6. Deploy

```bash
cd cloudflare
wrangler deploy
```

## 🌐 URLs nach Deployment

- **Static Site**: `https://zen-ai-pentest.pages.dev`
- **API Worker**: `https://zen-ai-pentest.your-subdomain.workers.dev`
- **Custom Domain**: `https://zen-ai-pentest.de` (optional)

## 📊 Features

### Kostenlos inklusive:

| Feature | Limit |
|---------|-------|
| Workers Requests | 100.000/Tag |
| Workers CPU Time | 10ms/Request |
| KV Reads | 100.000/Tag |
| KV Writes | 1.000/Tag |
| Pages Bandwidth | 1TB/Monat |
| Pages Builds | 500/Monat |

## 🔧 Konfiguration

### Custom Domain

```bash
# In Cloudflare Dashboard:
# 1. Workers & Pages → zen-ai-pentest
# 2. Triggers → Add Custom Domain
# 3. Domain: zen-ai-pentest.de
```

### Environment Variables

```bash
# Production
wrangler secret put JWT_SECRET --env production
wrangler secret put KIMI_API_KEY --env production

# Staging
wrangler secret put JWT_SECRET --env staging
```

## 📁 Projektstruktur

```
cloudflare/
├── src/
│   ├── index.js      # Haupt-Worker
│   ├── router.js     # URL Routing
│   ├── auth.js       # JWT Auth
│   └── cache.js      # KV Cache Wrapper
├── wrangler.toml     # Konfiguration
├── package.json      # Dependencies
└── README.md         # Diese Datei
```

## 🧪 Lokale Entwicklung

```bash
# Worker lokal starten
cd cloudflare
wrangler dev

# Mit lokalem Frontend
# Frontend: http://localhost:5173
# Worker API: http://localhost:8787
```

## 🔄 CI/CD

Automatisches Deployment bei Push auf `main`:

```yaml
# .github/workflows/deploy-cloudflare.yml
# Bereits konfiguriert!
```

Erforderliche GitHub Secrets:
- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

### API Token erstellen:

1. [Cloudflare Dashboard](https://dash.cloudflare.com/profile/api-tokens)
2. Create Token
3. Use Template: "Edit Cloudflare Workers"
4. Permissions:
   - Cloudflare Pages:Edit
   - Workers Scripts:Edit
   - Account:Read
   - Zone:Read

## 📈 Monitoring

### Wrangler Logs

```bash
wrangler tail
```

### Analytics

- [Cloudflare Dashboard](https://dash.cloudflare.com)
- Workers → zen-ai-pentest → Analytics

### Custom Analytics

```javascript
// In index.js
await env.ANALYTICS.writeDataPoint({
  blobs: ['request', url.pathname],
  doubles: [1, duration],
  indexes: ['api']
});
```

## 🔒 Sicherheit

- ✅ JWT Authentication
- ✅ Rate Limiting (Cloudflare)
- ✅ DDoS Protection
- ✅ WAF (Web Application Firewall)
- ✅ SSL/TLS automatisch

## 🐛 Troubleshooting

### Build fehlschlägt

```bash
# Cache löschen
wrangler deploy --clear-cache
```

### KV nicht gefunden

```bash
# Namespace ID prüfen
wrangler kv:namespace list
# In wrangler.toml aktualisieren
```

### Secrets nicht verfügbar

```bash
# Secret neu setzen
wrangler secret put JWT_SECRET
```

## 📚 Ressourcen

- [Cloudflare Workers Docs](https://developers.cloudflare.com/workers/)
- [Cloudflare Pages Docs](https://developers.cloudflare.com/pages/)
- [Wrangler CLI Docs](https://developers.cloudflare.com/workers/wrangler/)

## 💰 Kosten

**Kostenlos für:**
- Persönliche Projekte
- Kleine Teams
- Bis 100k Requests/Tag

**Paid Plan ($5/Monat):**
- 10 Millionen Requests/Monat
- Längere CPU-Zeit
- Mehr KV Storage

Mehr Infos: [Cloudflare Pricing](https://workers.cloudflare.com/)
