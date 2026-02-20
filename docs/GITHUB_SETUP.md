# GitHub Repository Setup Guide

Complete guide for configuring Zen AI Pentest GitHub repository with enterprise-grade settings.

## ✅ Current Status

Last updated: 2026-01-31

| Feature | Status | Notes |
|---------|--------|-------|
| Branch Protection | ✅ Active | Master protected, 1 review required |
| Security Scanning | ✅ Active | CodeQL, Secret Scanning, Dependabot |
| Vulnerability Alerts | ✅ Active | Auto-enabled |
| Wiki | ⚠️ Enabled but Empty | Auto-sync configured |
| Discussions | ✅ Enabled | Community Q&A |
| Projects | ✅ Enabled | Roadmap tracking |
| Actions | ✅ 16 Workflows | CI/CD, Security, Automation |
| Pages | ❌ Disabled | Can be enabled for docs |

---

## 🔒 Security Configuration

### Enabled Security Features

1. **Code Scanning (CodeQL)**
   - Runs on every PR and push to master
   - Schedule: Weekly (Sundays)
   - Languages: Python
   - Location: `.github/workflows/codeql.yml`

2. **Secret Scanning**
   - Alerts for exposed secrets
   - Push protection active
   - Checks: API keys, tokens, passwords

3. **Dependabot**
   - Weekly dependency updates
   - Auto-PR creation
   - Security alerts enabled
   - Auto-merge for patch updates

4. **Vulnerability Alerts**
   - Automatic notifications
   - CVE database integration
   - Fix suggestions

### Branch Protection Rules (Master)

```yaml
Require PR reviews: YES (1 approval)
Dismiss stale reviews: YES
Require CODEOWNERS: YES
Require status checks: YES (5 checks)
  - test (ubuntu-latest, 3.11)
  - test (ubuntu-latest, 3.12)
  - test (windows-latest, 3.11)
  - Analyze Python Code (CodeQL)
  - dependency-review
Force pushes: BLOCKED
Branch deletion: BLOCKED
Admin enforcement: YES
```

---

## 📋 Pull Request Workflow

### PR Validation

All PRs are automatically validated for:

1. **Title Format** - Conventional Commits
   ```
   <type>(<scope>): <description>

   Examples:
   - feat: add new agent system
   - fix: resolve CVE loading issue
   - docs: update API documentation
   - security: patch SQL injection
   - chore(deps): update dependencies
   ```

2. **Required Checks**
   - Code style (Black, isort, flake8)
   - Security scan (Bandit)
   - Tests (pytest)
   - CodeQL Analysis
   - Dependency review

3. **Auto-Labeling**
   - PRs are auto-labeled based on title
   - Labels: enhancement, bug, security, dependencies, etc.

### PR Templates

Available templates:
- Bug Report
- Feature Request
- CVE/Payload Submission
- Pentest Report
- Branch Protection Exception (emergency)

---

## 🤖 Actions Runners

### GitHub-Hosted Runners (Default)

```yaml
Strategy:
  OS: ubuntu-latest, windows-latest, macos-latest
  Python: 3.9, 3.10, 3.11, 3.12, 3.13
```

### Self-Hosted Runners (Optional)

To add self-hosted runners:

```bash
# 1. Go to Settings > Actions > Runners
# 2. Click "New self-hosted runner"
# 3. Follow OS-specific instructions
# 4. Configure labels (e.g., 'pentest', 'gpu', 'windows')
```

---

## 📚 Wiki Configuration

### Auto-Sync Setup

The wiki auto-syncs from:
- `README.md` → Home page
- `docs/*.md` → Wiki pages
- Trigger: Push to master

### Manual Wiki Edit

```bash
# Clone wiki
git clone https://github.com/SHAdd0WTAka/zen-ai-pentest.wiki.git

# Edit pages
cd zen-ai-pentest.wiki
echo "# New Page" > New-Page.md

# Commit and push
git add .
git commit -m "Add new page"
git push
```

---

## 💬 Discussions

### Categories

1. **Q&A** - Questions and answers
2. **Ideas** - Feature suggestions
3. **Show and Tell** - Share your projects
4. **General** - Everything else

### Templates

- General Discussion
- Q&A
- Ideas/Feature Requests

---

## 📊 Projects

### Recommended Project Boards

1. **Roadmap** - High-level planning
   - Columns: Backlog, To Do, In Progress, Review, Done

2. **Bug Triage** - Issue management
   - Columns: New, Confirmed, In Progress, Fixed, Closed

3. **Sprint Planning** - Iteration tracking
   - Columns: To Do, In Progress, Review, Done

---

## 🌐 GitHub Pages (Optional)

To enable for documentation:

1. Go to Settings > Pages
2. Source: Deploy from a branch
3. Branch: `gh-pages` / folder: `/ (root)`
4. Or use GitHub Actions for MkDocs

### MkDocs Deployment

```yaml
# .github/workflows/pages.yml
name: Deploy to GitHub Pages
on:
  push:
    branches: [master]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install mkdocs-material
      - run: mkdocs gh-deploy --force
```

---

## 🔄 Maintenance Tasks

### Weekly

- [ ] Review Dependabot PRs
- [ ] Check security alerts
- [ ] Review stale issues/PRs

### Monthly

- [ ] Update Actions versions
- [ ] Review branch protection rules
- [ ] Audit repository access

### Quarterly

- [ ] Review CODEOWNERS
- [ ] Update security policies
- [ ] Archive old releases

---

## 🚨 Emergency Procedures

### Bypass Branch Protection

Only for critical security fixes:

1. Create issue using "Branch Protection Exception" template
2. Contact repository admin
3. Temporarily disable protection (Settings > Branches)
4. Push fix directly
5. Re-enable protection immediately
6. Document incident

### Security Incident Response

1. Create private security advisory
2. Do NOT create public issue
3. Contact: security@zen-ai-pentest.dev
4. Response time: 48 hours

---

## 📈 Metrics Dashboard

### Available Insights

- Code frequency
- Dependency graph
- Traffic analytics
- Contribution graph
- Code scanning alerts

### Access

```
Repository > Insights > [Tab]
```

---

## 🔗 Quick Links

| Resource | URL |
|----------|-----|
| Settings | https://github.com/SHAdd0WTAka/zen-ai-pentest/settings |
| Branches | https://github.com/SHAdd0WTAka/zen-ai-pentest/settings/branches |
| Secrets | https://github.com/SHAdd0WTAka/zen-ai-pentest/settings/secrets/actions |
| Actions | https://github.com/SHAdd0WTAka/zen-ai-pentest/actions |
| Security | https://github.com/SHAdd0WTAka/zen-ai-pentest/security |
| Discussions | https://github.com/SHAdd0WTAka/zen-ai-pentest/discussions |
| Wiki | https://github.com/SHAdd0WTAka/zen-ai-pentest/wiki |

---

## 🆘 Support

For GitHub-related issues:
- [GitHub Docs](https://docs.github.com)
- [GitHub Support](https://support.github.com)
- [GitHub Community](https://github.community)

For Zen AI Pentest-specific issues:
- Open a [Discussion](../../discussions)
- Create an [Issue](../../issues)
- Email: support@zen-ai-pentest.dev
