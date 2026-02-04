# Branch Protection Setup Guide

This guide explains how to configure branch protection rules for the Zen AI Pentest repository.

## Quick Setup

### 1. Navigate to Branch Protection Settings

1. Go to: `https://github.com/SHAdd0WTAka/Zen-Ai-Pentest/settings/branches`
2. Click "Add rule" next to "Branch protection rules"

### 2. Branch Name Pattern

Enter: `master` (or `main` if using main)

### 3. Enable Protection Rules

Check the following boxes:

#### ✅ Require a pull request before merging
- **Require approvals**: Set to `1` (or more for critical repos)
- **Dismiss stale PR approvals when new commits are pushed**: ✅
- **Require review from Code Owners**: ✅ (optional)

#### ✅ Require status checks to pass before merging
Search for and enable these status checks:
- `backend (3.13)` - Python tests
- `frontend` - Node.js build
- `pre-commit` - Pre-commit hooks
- `migrations` - Database migration check
- `docker` - Docker build test
- `ci-summary` - Overall CI status

#### ✅ Require branches to be up to date before merging

#### ✅ Require conversation resolution before merging

#### ✅ Require signed commits (optional but recommended)

#### ✅ Include administrators
(Admins should also follow the rules)

#### 🚫 Restrict pushes that create files larger than 100 MB

#### ✅ Block force pushes

#### ✅ Block deletions

### 4. Save Changes

Click "Create" or "Save changes"

---

## Advanced Settings

### For `develop` Branch (if using GitFlow)

Create a second rule with pattern: `develop`

Use lighter restrictions:
- Require PR: ✅ (1 approval)
- Require status checks: ✅ (basic tests only)
- Allow force pushes: ❌

---

## Verification

After setup, test the protection:

1. Create a new branch: `git checkout -b test-protection`
2. Make a small change and commit
3. Try to push directly to master:
   ```bash
   git push origin master
   ```
4. **Expected**: Error message about branch protection
5. Create a Pull Request instead:
   ```bash
   git push origin test-protection
   # Then create PR on GitHub
   ```

---

## Troubleshooting

### Status checks not appearing?
- They only appear after the first workflow run
- Push any change to trigger CI first

### Emergency bypass?
Repository admins can still bypass if "Include administrators" is unchecked, but this is NOT recommended.

### Required reviews too slow?
Consider CODEOWNERS file for automatic reviewer assignment.

---

## CODEOWNERS (Optional)

Create `.github/CODEOWNERS`:

```
# Global default
* @SHAdd0WTAka

# Security-sensitive files
.github/workflows/ @SHAdd0WTAka
api/auth*.py @SHAdd0WTAka
database/models.py @SHAdd0WTAka
```

This automatically requests reviews from specified users.

---

**Last Updated**: 2026-02-04
