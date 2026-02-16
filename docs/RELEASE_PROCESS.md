# Release Process

This document describes how to create and publish releases for Zen-AI-Pentest.

---

## Overview

Zen-AI-Pentest follows [Semantic Versioning](https://semver.org/) (SemVer) and uses automated release processes through GitHub Actions.

| Version Format | Description | Example |
|----------------|-------------|---------|
| `MAJOR.MINOR.PATCH` | Standard releases | `2.3.9` |
| `MAJOR.MINOR.PATCH-beta.N` | Beta releases | `2.4.0-beta.1` |
| `MAJOR.MINOR.PATCH-alpha.N` | Alpha releases | `2.4.0-alpha.1` |

---

## Release Checklist

Before creating a release, ensure:

- [ ] All tests pass (`pytest`)
- [ ] Security scans pass (`bandit`, `safety`)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in:
  - [ ] `zen_ai_pentest/__init__.py`
  - [ ] `setup.py`
  - [ ] `pyproject.toml`
- [ ] Git tag created
- [ ] Release notes drafted

---

## Automated Release Process

### Standard Release (Patch/Minor)

1. **Create a release PR**
   ```bash
   git checkout -b release/v2.3.10
   # Update version numbers
   git commit -m "chore: bump version to 2.3.10"
   git push origin release/v2.3.10
   ```

2. **Merge to main**
   - Create PR
   - Get review (required)
   - Merge when CI passes

3. **Create Git tag**
   ```bash
   git checkout main
   git pull
   git tag -a v2.3.10 -m "Release version 2.3.10"
   git push origin v2.3.10
   ```

4. **Automated publication**
   - GitHub Actions detects tag
   - Builds packages
   - Creates GitHub Release
   - Publishes to PyPI (trusted publishing)
   - Sends notifications

### Hotfix Release

For critical security fixes:

1. **Create hotfix branch from latest tag**
   ```bash
   git checkout -b hotfix/v2.3.10 v2.3.9
   ```

2. **Apply fix**
   ```bash
   # Make minimal fix
   git commit -m "security: fix critical vulnerability"
   ```

3. **Fast-track release**
   - Skip some CI checks if necessary (document why)
   - Emergency review process
   - Immediate deployment

---

## Manual Release Steps

If automated process fails:

### 1. Build Package

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build
python -m build

# Verify
twine check dist/*
```

### 2. Test Installation

```bash
# Create fresh venv
python -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate

# Install
pip install dist/zen_ai_pentest-*.whl

# Test
zen-ai-pentest --version
```

### 3. Create GitHub Release

1. Go to: https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/releases
2. Click "Draft a new release"
3. Choose tag: `v2.3.10`
4. Title: `Version 2.3.10`
5. Description: Copy from CHANGELOG.md
6. Attach binaries (optional)
7. Publish

### 4. Publish to PyPI

```bash
# Using trusted publishing (recommended)
# Already done by GitHub Actions

# Manual fallback (requires credentials)
twine upload dist/*
```

---

## Pre-release Versions

### Alpha Releases

- **Purpose**: Internal testing
- **Format**: `2.4.0-alpha.1`
- **Stability**: Unstable, features may change
- **Distribution**: GitHub only (not PyPI)

```bash
git tag -a v2.4.0-alpha.1 -m "Alpha release 2.4.0-alpha.1"
git push origin v2.4.0-alpha.1
```

### Beta Releases

- **Purpose**: Public testing
- **Format**: `2.4.0-beta.1`
- **Stability**: Feature-complete, bugs expected
- **Distribution**: PyPI with `--pre` flag

```bash
git tag -a v2.4.0-beta.1 -m "Beta release 2.4.0-beta.1"
git push origin v2.4.0-beta.1
```

---

## Release Notes Template

```markdown
## What's New in Version 2.3.10

### 🚀 Features
- Feature 1 description
- Feature 2 description

### 🐛 Bug Fixes
- Fix 1 description (#123)
- Fix 2 description (#124)

### 🔒 Security
- Security fix description (if any)

### 📚 Documentation
- Doc updates

### 🔄 Deprecations
- Deprecated features (if any)

### 💥 Breaking Changes
- Breaking changes (if any)

**Full Changelog**: https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/blob/main/CHANGELOG.md
```

---

## Security Releases

### Security Advisory Process

1. **Private Disclosure**
   - Use GitHub Security Advisories
   - Do NOT create public issue

2. **Fix Development**
   - Create private fix branch
   - Review by security team

3. **Coordinated Disclosure**
   - Release fix
   - Publish advisory
   - Notify users

4. **Post-Release**
   - Update documentation
   - Monitor for variants

### Security Release Format

Version: `2.3.10-security.1`

```markdown
## Security Release 2.3.10

### 🛡️ Security Fix
Fixed [CVE-XXXX-XXXXX]: Brief description

**Severity**: [Critical/High/Medium/Low]
**Affected Versions**: < 2.3.10
**Patched Versions**: >= 2.3.10

### Upgrade Instructions
```bash
pip install --upgrade zen-ai-pentest
```

**Credit**: Reporter name (if disclosed)
```

---

## Rollback Procedure

If a release is broken:

1. **Immediate action**
   - Yank from PyPI: `twine delete zen-ai-pentest-2.3.10`
   - Mark GitHub release as pre-release

2. **Communication**
   - Post incident report
   - Notify users via Discord/Telegram

3. **Fix and re-release**
   - Fix the issue
   - Release as 2.3.11

---

## Automated Checks

Every release automatically:

| Check | Tool | Required |
|-------|------|----------|
| Tests | pytest | ✅ Yes |
| Security | bandit, safety | ✅ Yes |
| Linting | ruff | ✅ Yes |
| Type Check | mypy | ⚠️ Optional |
| Build | build | ✅ Yes |
| Signatures | sigstore | ✅ Yes |

---

## Contact

For release questions:
- @SHAdd0WTAka (Release Manager)
- @Kimi AI (Technical Lead)

---

*This document is maintained by ZenClaw Guardian.*
