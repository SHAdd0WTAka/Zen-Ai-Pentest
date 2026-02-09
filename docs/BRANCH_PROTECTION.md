# Branch Protection Setup Guide

## ⚠️ CRITICAL: Your Master Branch is Unprotected!

This guide will help you configure branch protection for the `master`/`main` branch to secure your repository.

---

## 🎯 Why Branch Protection Matters

### Security Risks of Unprotected Branches:
- **Force Pushes**: Malicious actors can rewrite git history
- **Direct Pushes**: Code can be committed without review
- **No Quality Gates**: Broken code can be merged
- **Accidental Deletion**: Branch can be deleted
- **Compliance Issues**: Many security standards require branch protection

### Benefits:
- ✅ Mandatory code review
- ✅ Required automated testing
- ✅ Prevent accidental force pushes
- ✅ Audit trail for all changes
- ✅ Compliance with security standards (SOC2, ISO27001)

---

## 🔧 Configuration Steps

### Method 1: Manual Configuration (Recommended)

1. **Navigate to Settings**
   ```
   Repository → Settings → Branches
   ```

2. **Add Protection Rule**
   - Click "Add rule" (next to "Branch protection rules")
   - Branch name pattern: `master` (or `main`)

3. **Configure Protection Settings**

   #### ☑️ Require a pull request before merging
   ```
   ✓ Require approvals (minimum: 1)
   ✓ Dismiss stale PR approvals when new commits are pushed
   ✓ Require review from CODEOWNERS
   ✓ Restrict who can dismiss pull request reviews
   ```

   #### ☑️ Require status checks to pass before merging
   ```
   ✓ Require branches to be up to date before merging
   
   Required checks:
   - test (ubuntu-latest, 3.11)
   - test (ubuntu-latest, 3.12)
   - test (windows-latest, 3.11)
   - Analyze Python Code (CodeQL)
   - dependency-review
   ```

   #### ☑️ Require conversation resolution before merging
   ```
   ✓ Required
   ```

   #### ☑️ Restrict pushes that create files larger than 100MB
   ```
   ✓ Enabled
   ```

   #### ☑️ Do not allow bypassing the above settings
   ```
   ✓ Apply to administrators
   ```

   #### ☑️ Restrict who can push to matching branches
   ```
   ✓ Restrict pushes that create matching branches
   ✓ Allow force pushes: NO
   ✓ Allow deletions: NO
   ```

4. **Save Changes**
   - Click "Create" or "Save changes"

---

### Method 2: Using Probot Settings App

1. **Install Probot Settings**
   - Go to: https://github.com/apps/settings
   - Click "Install"
   - Select your repository
   - Grant necessary permissions

2. **Configuration File**
   The `.github/settings.yml` file in this repository already contains the recommended settings. Once Probot is installed, it will automatically apply these settings.

3. **Verify Settings**
   - Check `Settings → Branches` to confirm protection is active
   - Review the applied rules

---

## 📋 Recommended Settings Summary

| Setting | Value | Reason |
|---------|-------|--------|
| Require PR reviews | 1 approval | Code review requirement |
| Dismiss stale reviews | Enabled | Ensure fresh reviews |
| Require CODEOWNERS | Enabled | Domain expert review |
| Require status checks | Enabled | Quality assurance |
| Up-to-date branches | Enabled | Prevent merge conflicts |
| Force pushes | Disabled | Prevent history rewrite |
| Branch deletion | Disabled | Prevent data loss |
| Conversation resolution | Enabled | Ensure all comments addressed |

---

## ✅ Verification

### Check Protection Status
```bash
# Using GitHub CLI
git branch protection view master

# Or via API
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/SHAdd0WTAka/zen-ai-pentest/branches/master/protection
```

### Automated Check
A GitHub Actions workflow (`.github/workflows/branch-protection-check.yml`) runs daily to verify branch protection is enabled and creates an issue if not.

---

## 🔐 Advanced Security Settings

### Additional Recommendations

1. **Signed Commits**
   ```
   Settings → Branches → Require signed commits
   ```

2. **Linear History**
   ```
   Settings → Branches → Require linear history
   ```

3. **Push Restrictions**
   - Limit who can push to specific teams
   - Require SSH keys for push access

4. **Deployment Protection**
   ```
   Settings → Environments
   Configure protection rules for production
   ```

---

## 🚨 Troubleshooting

### Issue: Cannot push to master
**Solution**: Create a feature branch and open a pull request
```bash
git checkout -b feature/my-feature
git push origin feature/my-feature
# Open PR via GitHub UI
```

### Issue: Status checks not running
**Solution**: Ensure workflows are enabled in Actions tab
```
Settings → Actions → General → Allow all actions
```

### Issue: CODEOWNERS not working
**Solution**: Verify CODEOWNERS file exists and is valid
```bash
# Check syntax
cat CODEOWNERS
```

---

## 📊 Compliance Mapping

| Standard | Requirement | Branch Protection |
|----------|-------------|-------------------|
| SOC 2 | Change Management | ✅ Required |
| ISO 27001 | Access Control | ✅ Required |
| PCI DSS | Secure Development | ✅ Required |
| NIST 800-53 | Configuration Management | ✅ Required |

---

## 🔗 Related Documentation

- [GitHub Docs: Protected Branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [Security Policy](../SECURITY.md)
- [Contributing Guidelines](../CONTRIBUTING.md)
- [CODEOWNERS Info](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)

---

## 🆘 Need Help?

If you need assistance configuring branch protection:

1. Check the automated workflow logs: `Actions → Branch Protection Check`
2. Review the [troubleshooting section](#-troubleshooting)
3. Open a [discussion](../../discussions) for questions
4. Contact the security team for critical issues

---

**Last Updated**: 2026-01-31  
**Next Review**: 2026-04-30
