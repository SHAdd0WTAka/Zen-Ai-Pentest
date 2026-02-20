# Security Update Instructions

## Overview
The `package.json` has been updated to fix 4 medium severity CVEs.
To complete the security update, you need to regenerate `package-lock.json`.

## Changes Made to package.json

### Updated Packages:
- `vite`: ^5.0.0 → ^5.4.14
- `axios`: ^1.6.0 → ^1.7.4

### Added Security Overrides:
```json
"overrides": {
  "esbuild": "^0.21.5",
  "jsonpath": "^1.1.1",
  "webpack-dev-server": "^5.0.4"
}
```

## Steps to Complete Update

### 1. Navigate to dashboard directory:
```bash
cd zen-ai-pentest/web_ui/dashboard
```

### 2. Remove old lock file:
```bash
rm package-lock.json
```

### 3. Install dependencies (generates new lock file):
```bash
npm install
```

### 4. Verify no vulnerabilities remain:
```bash
npm audit
```

Expected output:
```
found 0 vulnerabilities
```

### 5. Test the build:
```bash
npm run build
```

### 6. Commit the new lock file:
```bash
git add package-lock.json
git commit -m "chore(security): regenerate package-lock.json

- Fixes 4 medium severity CVEs
- Updates transitive dependencies via overrides
- Verified with npm audit (0 vulnerabilities)"
git push
```

## Vulnerabilities Fixed

| Package | Issue | Severity |
|---------|-------|----------|
| esbuild | Arbitrary file read | Medium |
| jsonpath | Prototype Pollution | Medium |
| webpack-dev-server | Source code exposure | Medium |
| axios | Security patches | Medium |

## Verification Commands

```bash
# Check for vulnerabilities
npm audit

# Check outdated packages
npm outdated

# Run linter
npm run lint

# Build project
npm run build
```

## Notes

- The `overrides` section in package.json forces specific versions of vulnerable transitive dependencies
- This ensures security even if direct dependencies haven't updated their requirements
- After running `npm install`, verify the lock file was generated correctly
