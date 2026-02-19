# 🛠️ Developer Tools & Integrations

## Must-Have Tools (Kostenlos)

### 1. Code Quality

| Tool | Zweck | Einrichtung |
|------|-------|-------------|
| **Codecov** | Test Coverage Reports | `.github/codecov.yml` ✅ |
| **DeepSource** | Automatische Code Review | `.deepsource.toml` ✅ |
| **Codacy** | Code Quality Gates | `.codacy.yml` ✅ |
| **SonarCloud** | Security & Quality Analysis | [sonarcloud.io](https://sonarcloud.io) |

### 2. Security Scanning

| Tool | Zweck | Status |
|------|-------|--------|
| **GitHub Dependabot** | Dependency Updates | ✅ Aktiviert |
| **GitHub CodeQL** | SAST Security Analysis | ✅ Aktiviert |
| **Snyk** | Vulnerability Scanner | [snyk.io](https://snyk.io) |
| **FOSSA** | License Compliance | [fossa.com](https://fossa.com) |

### 3. Documentation

| Tool | Zweck | Link |
|------|-------|------|
| **Read the Docs** | Documentation Hosting | [readthedocs.org](https://readthedocs.org) |
| **MkDocs Material** | Static Doc Generator | ✅ Installiert |
| **Swagger UI** | API Documentation | ✅ `/docs` Endpoint |

### 4. CI/CD Enhancements

```yaml
# .github/workflows/enhanced-ci.yml
name: Enhanced CI

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      # Codecov
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          fail_ci_if_error: true
      
      # DeepSource
      - name: DeepSource Analysis
        uses: deepsourcelabs/deepsource-action@v1
        with:
          dsn: ${{ secrets.DEEPSOURCE_DSN }}
      
      # SonarCloud
      - name: SonarCloud Scan
        uses: SonarSource/sonarcloud-github-action@master
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
```

## 🌐 Cloudflare Setup (Kostenlos)

### Option 1: Cloudflare Pages (Static Site)

**Für das Mirror Website:**

1. **Repository verbinden:**
   - Gehe zu [dash.cloudflare.com](https://dash.cloudflare.com)
   - Pages → Create a project → Connect to Git
   - Wähle `Zen-Ai-Pentest` Repo

2. **Build Settings:**
```yaml
# cloudflare-pages.yml
build_command: "cd web_ui/frontend && npm run build"
build_output_directory: "web_ui/frontend/dist"
root_directory: ""
```

3. **Environment Variables:**
```bash
NODE_VERSION: 20
VITE_API_URL: https://api.zen-ai-pentest.workers.dev
```

### Option 2: Cloudflare Workers (API + Frontend)

**Vorteile:**
- ✅ Kostenlos: 100.000 Requests/Tag
- ✅ Edge-Location weltweit
- ✅ Eigene Domain möglich
- ✅ DDoS Protection

**wrangler.toml:**
```toml
name = "zen-ai-pentest"
main = "workers/index.js"
compatibility_date = "2026-02-19"

[site]
bucket = "./web_ui/frontend/dist"

[env.production]
vars = { ENVIRONMENT = "production" }

[[env.production.kv_namespaces]]
binding = "CACHE"
id = "your-kv-namespace-id"
```

### Option 3: Cloudflare Tunnel (lokaler Server)

**Für Entwicklung/Private Instanz:**

```bash
# Installation
brew install cloudflared

# Tunnel erstellen
cloudflared tunnel create zen-pentest

# Konfiguration
cloudflared tunnel route dns zen-pentest zen-ai-pentest.yourdomain.com

# Config.yml
tunnel: <tunnel-id>
credentials-file: /path/to/credentials.json

ingress:
  - hostname: zen-ai-pentest.yourdomain.com
    service: http://localhost:8080
  - service: http_status:404
```

## 📊 Monitoring & Analytics (Kostenlos)

### Uptime Monitoring

```yaml
# .github/workflows/uptime.yml
name: Uptime Monitor

on:
  schedule:
    - cron: '*/5 * * * *'  # Alle 5 Minuten

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - name: Check API Health
        run: |
          curl -f https://api.zen-ai-pentest.workers.dev/health || exit 1
      
      - name: Notify on Failure
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          payload: '{"text":"🚨 Zen-AI-Pentest API is DOWN!"}'
```

### Analytics Dashboard

| Tool | Zweck | Kosten |
|------|-------|--------|
| **Plausible** | Privacy-First Analytics | Self-hosted / Cloud |
| **Umami** | Open Source Analytics | Self-hosted |
| **Cloudflare Analytics** | Edge Analytics | ✅ Kostenlos |

## 🔧 Lokale DevTools

### VS Code Extensions (Empfohlen)

```json
// .vscode/extensions.json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "dbaeumer.vscode-eslint",
    "bradlc.vscode-tailwindcss",
    "ms-vscode.vscode-typescript-next",
    "github.copilot",
    "github.copilot-chat",
    "eamodio.gitlens",
    "usernamehw.errorlens",
    "streetsidesoftware.code-spell-checker",
    "yzhang.markdown-all-in-one",
    "redhat.vscode-yaml",
    "ms-azuretools.vscode-docker",
    "ms-vscode-remote.remote-wsl",
    "ritwickdey.LiveServer",
    "ms-vscode.vscode-json"
  ]
}
```

### Git Hooks (Husky)

```bash
# Installation
npx husky-init && npm install

# Pre-commit hook
npx husky add .husky/pre-commit "npm run lint && npm run test"
```

## 🚀 Quick Setup Commands

```bash
# Alle Tools installieren
make setup-devtools

# Code Quality Checks
make lint          # ESLint + Black
make test          # pytest + coverage
make security      # Bandit + Safety

# Cloudflare Deploy
make deploy-cloudflare  # Workers deploy
make deploy-pages       # Pages deploy
```

## 📈 Performance Budget

```yaml
# .github/lighthouse.yml
name: Lighthouse CI

on: [push]

jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Audit URLs
        uses: treosh/lighthouse-ci-action@v11
        with:
          urls: |
            https://zen-ai-pentest.pages.dev/
          budgetPath: ./budget.json
```

## 🔐 Security Best Practices

1. **Secrets Management:**
   - GitHub Secrets für CI/CD
   - Cloudflare Secrets für Workers
   - `.env.example` im Repo (ohne echte Werte)

2. **Dependency Scanning:**
   - Snyk: `npx snyk test`
   - npm audit: `npm audit fix`
   - pip-audit: `pip-audit`

3. **Code Signing:**
   - GPG commits: `git commit -S`
   - Sigstore für Releases
