# Cloudflare API Token Setup für GitHub Actions

## Schritt 1: API Token erstellen

1. Gehe zu: https://dash.cloudflare.com/profile/api-tokens
2. Klicke: **"Create Token"**
3. Wähle: **"Edit Cloudflare Workers"** Template
4. Passe die Permissions an:

```
Account Resources:
  - Include: Dein Account

Zone Resources:
  - Include: All zones (oder spezifische Domain)

Permissions:
  - Cloudflare Pages: Edit
  - Workers Scripts: Edit  
  - Workers Routes: Edit
  - Workers KV Storage: Edit
  - Account: Read
  - Zone: Read
```

5. Klicke **"Continue to summary"**
6. Klicke **"Create Token"**
7. **Kopiere den Token** (wird nur einmal angezeigt!)

## Schritt 2: GitHub Secrets hinzufügen

1. Gehe zu deinem GitHub Repo
2. Settings → Secrets and variables → Actions
3. Klicke **"New repository secret"**
4. Füge hinzu:

| Name | Wert |
|------|------|
| `CLOUDFLARE_API_TOKEN` | Dein API Token |
| `CLOUDFLARE_ACCOUNT_ID` | Siehe unten |

## Account ID finden

1. Gehe zu: https://dash.cloudflare.com
2. Rechts in der Sidebar steht die **Account ID**
3. Kopiere sie

## Schritt 3: KV Namespace erstellen

```bash
# Mit wrangler CLI (einmalig)
wrangler login
wrangler kv:namespace create CACHE
# Oder über Cloudflare Dashboard:
# Workers & Pages → KV → Create namespace
```

Die KV Namespace ID wird im GitHub Workflow automatisch verwendet oder du trägst sie in `wrangler.toml` ein.

## Schritt 4: Testen

Nachdem die Secrets gesetzt sind, pushe etwas auf den `main` Branch:

```bash
git add .
git commit -m "chore: setup cloudflare deployment"
git push origin main
```

Der Workflow wird automatisch starten unter:
**Actions → Deploy to Cloudflare**
