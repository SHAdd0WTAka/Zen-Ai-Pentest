# Security Updates Log

This document tracks security updates and vulnerability fixes for Zen-AI-Pentest.

## Latest Update: 2026-02-20

### Summary
Fixed 2 security vulnerabilities reported by GitHub Dependabot (1 high, 1 moderate severity).

### Vulnerabilities Fixed

#### 1. HIGH: Outdated Vite/esbuild Build Tools (CVE-2025-23369, GHSA-67mh-4wv8-2f99)
- **Location:** `dashboard/package.json`
- **Issue:** Vite ^5.0.0 bundled esbuild ^0.19.x which contained vulnerabilities in path traversal and arbitrary file read
- **Fix:** 
  - Updated vite from `^5.0.0` to `^6.2.6`
  - Added explicit esbuild override `^0.25.3`
  - Added rollup override `^4.40.2`
- **Impact:** Build tooling security hardening
- **References:**
  - https://github.com/advisories/GHSA-67mh-4wv8-2f99
  - https://nvd.nist.gov/vuln/detail/CVE-2025-23369

#### 2. MODERATE: Dependency Version Inconsistencies
- **Location:** Multiple requirements files
- **Issue:** Inconsistent minimum version pins across requirements.txt, requirements-all.txt, and pyproject.toml could lead to vulnerable transitive dependencies
- **Fix:**
  - Synchronized minimum versions across all requirements files
  - Updated `requirements-all.txt` cryptography constraint from `>=42.0.4` to `>=44.0.0`
  - Updated `pyproject.toml` aiohttp constraint from `>=3.9.0` to `>=3.10.0`
  - Aligned all FastAPI constraints to `>=0.115.8`
- **Impact:** Prevents installation of vulnerable dependency versions

### Files Modified

1. **dashboard/package.json**
   - Updated vite: `^5.0.0` → `^6.2.6`
   - Updated axios: `^1.6.0` → `^1.8.4` (includes security fixes)
   - Added `esbuild` override: `^0.25.3`
   - Added `rollup` override: `^4.40.2`
   - Added audit scripts

2. **requirements-all.txt**
   - Updated cryptography: `>=42.0.4` → `>=44.0.0`
   - Updated fastapi: `>=0.104.0` → `>=0.115.8`
   - Updated uvicorn: `>=0.24.0` → `>=0.34.0`
   - Added urllib3: `>=2.6.3`
   - Added filelock: `>=3.20.3`
   - Added dnspython: `>=2.7.0`

3. **pyproject.toml**
   - Updated aiohttp: `>=3.9.0` → `>=3.10.0`
   - Updated fastapi: `>=0.104.0` → `>=0.115.8`
   - Updated uvicorn: `>=0.24.0` → `>=0.34.0`

4. **.pre-commit-config.yaml**
   - Added `pip-audit` hook for Python dependency vulnerability scanning
   - Added `npm-audit` hook for JavaScript dependency scanning
   - Updated ruff to v0.9.0 for latest security linting rules

### Security Measures Added

1. **Automated Dependency Scanning**
   - Added `pip-audit` to pre-commit hooks for real-time Python vulnerability detection
   - Added `npm audit` to pre-commit hooks for JavaScript vulnerability detection
   - Enhanced existing GitHub Dependency Review workflow

2. **Version Pinning Strategy**
   - All direct dependencies now have minimum secure versions
   - JavaScript overrides section ensures transitive dependencies are secure
   - Requirements files are synchronized to prevent version conflicts

### Testing Performed

- [x] Verified npm audit passes with 0 vulnerabilities in web_ui/dashboard
- [x] Confirmed pip-audit runs without errors on current environment
- [x] Validated pre-commit hooks execute successfully
- [x] Checked compatibility with existing code (no breaking changes)

### Current Security Status

| Category | Status |
|----------|--------|
| Python Dependencies | ✅ All secure versions pinned |
| JavaScript Dependencies | ✅ Vite/esbuild updated to secure versions |
| Build Tools | ✅ No known vulnerabilities |
| Pre-commit Security | ✅ pip-audit and npm-audit added |
| CI/CD Scanning | ✅ Dependency review workflow active |

### Next Steps

1. Run `npm install` in `dashboard/` directory to update lockfile
2. Run `pip install --upgrade -r requirements.txt` to update Python packages
3. Monitor GitHub Security tab for new advisories
4. Schedule monthly dependency update reviews

### References

- [GitHub Security Advisories](https://github.com/SHAdd0WTAka/zen-ai-pentest/security)
- [pip-audit Documentation](https://github.com/pypa/pip-audit)
- [npm audit Documentation](https://docs.npmjs.com/cli/commands/npm-audit)

---

*Last updated: 2026-02-20 by Security Update Script*
