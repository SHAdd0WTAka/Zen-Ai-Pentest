# NPM Package Lock Update Guide

## Quick Start

```bash
cd zen-ai-pentest/web_ui/dashboard
rm package-lock.json
npm install
npm audit
npm run build
git add package-lock.json
git commit -m "chore(security): regenerate package-lock.json to fix CVEs

- Updates transitive dependencies via security overrides
- Fixes 4 medium severity Dependabot alerts
- Verified: npm audit shows 0 vulnerabilities"
git push
```

## What This Fixes

| Package | CVE | Severity |
|---------|-----|----------|
| esbuild | Arbitrary file read | Medium |
| jsonpath | Prototype Pollution | Medium |
| webpack-dev-server | Source code exposure | Medium |

## Verification

After running `npm audit`, you should see:
```
found 0 vulnerabilities
```

## Troubleshooting

If build fails:
```bash
npm run lint
npm run type-check
```
