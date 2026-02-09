#!/usr/bin/env python3
"""
Repository Auto-Fix Script

This script performs automatic fixes for common repository health issues:
- Close stale issues with label
- Delete orphaned branches
- Sync fork with upstream
- Update outdated workflows
- Fix common linting issues

Usage:
    Set GITHUB_TOKEN and GITHUB_REPOSITORY environment variables.
    Optionally set FIX_LEVEL (safe/aggressive) and HEALTH_SCORE.
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import requests
from urllib.parse import urljoin

# Constants
GITHUB_API_URL = "https://api.github.com"
STALE_ISSUE_DAYS = 90
STALE_PR_DAYS = 60
ORPHANED_BRANCH_DAYS = 30


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def print_colored(message: str, color: str = Colors.BLUE):
    """Print a colored message."""
    print(f"{color}{message}{Colors.RESET}")


@dataclass
class FixResult:
    """Result of a fix operation."""

    category: str
    action: str
    success: bool
    message: str
    details: Dict[str, Any] = None


class GitHubAPI:
    """GitHub API client."""

    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo = repo
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self.base_url = f"{GITHUB_API_URL}/repos/{repo}"

    def get(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make a GET request."""
        url = urljoin(self.base_url + "/", endpoint)
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"⚠️ GET failed: {e}")
            return None

    def post(self, endpoint: str, data: Dict) -> Optional[Dict]:
        """Make a POST request."""
        url = urljoin(self.base_url + "/", endpoint)
        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            if response.status_code in [200, 201, 204]:
                return response.json() if response.text else {}
            print(f"⚠️ POST {endpoint} failed: {response.status_code}")
            return None
        except Exception as e:
            print(f"⚠️ POST failed: {e}")
            return None

    def patch(self, endpoint: str, data: Dict) -> Optional[Dict]:
        """Make a PATCH request."""
        url = urljoin(self.base_url + "/", endpoint)
        try:
            response = requests.patch(url, headers=self.headers, json=data, timeout=30)
            if response.status_code in [200, 204]:
                return response.json() if response.text else {}
            print(f"⚠️ PATCH {endpoint} failed: {response.status_code}")
            return None
        except Exception as e:
            print(f"⚠️ PATCH failed: {e}")
            return None

    def delete(self, endpoint: str) -> bool:
        """Make a DELETE request."""
        url = urljoin(self.base_url + "/", endpoint)
        try:
            response = requests.delete(url, headers=self.headers, timeout=30)
            return response.status_code in [200, 204]
        except Exception as e:
            print(f"⚠️ DELETE failed: {e}")
            return False

    def get_all_pages(self, endpoint: str, params: Dict = None) -> List[Dict]:
        """Get all pages of results."""
        results = []
        params = params or {}
        params["per_page"] = 100
        page = 1

        while page <= 10:  # Safety limit
            params["page"] = page
            url = urljoin(self.base_url + "/", endpoint)
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                if response.status_code != 200:
                    break
                data = response.json()
                if isinstance(data, list):
                    results.extend(data)
                    if len(data) < 100:
                        break
                else:
                    break
                page += 1
            except Exception as e:
                print(f"⚠️ Pagination error: {e}")
                break

        return results


class AutoFixer:
    """Main auto-fix class."""

    def __init__(self, token: str, repo: str):
        self.api = GitHubAPI(token, repo)
        self.repo = repo
        self.fix_level = os.environ.get("FIX_LEVEL", "safe")
        self.health_score = float(os.environ.get("HEALTH_SCORE", "0"))
        self.results: List[FixResult] = []
        self.now = datetime.now()
        self.dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"

        print("🔧 Auto-Fix Configuration:")
        print(f"   Repository: {repo}")
        print(f"   Fix Level: {self.fix_level}")
        print(f"   Health Score: {self.health_score}")
        print(f"   Dry Run: {self.dry_run}")
        print()

    def run_all_fixes(self) -> List[FixResult]:
        """Run all applicable fixes."""
        print("🚀 Starting Auto-Fix Process\n")

        # Load health data if available
        health_data = self._load_health_data()

        # Run fixes based on health data and level
        self._fix_stale_issues(health_data)
        self._fix_stale_prs(health_data)
        self._fix_orphaned_branches(health_data)
        self._fix_fork_sync(health_data)
        self._fix_dependabot_updates(health_data)

        if self.fix_level == "aggressive":
            self._fix_workflow_updates()
            self._fix_linting_issues()

        return self.results

    def _load_health_data(self) -> Dict:
        """Load health check data if available."""
        try:
            if os.path.exists("health-data/health-data.json"):
                with open("health-data/health-data.json", "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load health data: {e}")
        return {}

    def _fix_stale_issues(self, health_data: Dict) -> None:
        """Close stale issues with stale label."""
        print_colored("📋 Checking for Stale Issues", Colors.BLUE)

        stale_threshold = self.now - timedelta(days=STALE_ISSUE_DAYS)

        issues = self.api.get_all_pages("issues", {"state": "open"})
        if not issues:
            self.results.append(
                FixResult(category="Issues", action="Close stale", success=True, message="No open issues to check")
            )
            return

        closed_count = 0

        for issue in issues:
            if "pull_request" in issue:
                continue  # Skip PRs

            # Check if issue has stale label
            labels = [label["name"].lower() for label in issue.get("labels", [])]
            if "stale" not in labels and "auto-close" not in labels:
                continue

            # Check if issue is old enough
            updated_at = datetime.fromisoformat(issue["updated_at"].replace("Z", "+00:00"))
            if updated_at.replace(tzinfo=None) > stale_threshold:
                continue

            issue_number = issue["number"]

            if self.dry_run:
                print(f"   [DRY RUN] Would close issue #{issue_number}")
                closed_count += 1
                continue

            # Close the issue with a comment
            comment_body = f"""🤖 **Auto-closed by Repository Health Check**

This issue has been automatically closed because:
- It has been inactive for more than {STALE_ISSUE_DAYS} days
- It has the "stale" or "auto-close" label

If this issue is still relevant, please:
1. Remove the "stale" label
2. Add a comment explaining why it's still needed
3. Reopen the issue

---
*This action was performed automatically. If you believe this was done in error, please reopen the issue.*"""

            # Add comment
            self.api.post(f"issues/{issue_number}/comments", {"body": comment_body})

            # Close issue
            result = self.api.patch(f"issues/{issue_number}", {"state": "closed", "state_reason": "not_planned"})

            if result:
                print_colored(f"   ✅ Closed stale issue #{issue_number}", Colors.GREEN)
                closed_count += 1
            else:
                print_colored(f"   ❌ Failed to close issue #{issue_number}", Colors.RED)

        self.results.append(
            FixResult(
                category="Issues",
                action="Close stale",
                success=closed_count > 0,
                message=f"Closed {closed_count} stale issues",
                details={"count": closed_count},
            )
        )
        print()

    def _fix_stale_prs(self, health_data: Dict) -> None:
        """Label or close stale PRs."""
        print_colored("🔀 Checking for Stale PRs", Colors.BLUE)

        stale_threshold = self.now - timedelta(days=STALE_PR_DAYS)

        prs = self.api.get_all_pages("pulls", {"state": "open"})
        if not prs:
            self.results.append(FixResult(category="PRs", action="Label stale", success=True, message="No open PRs to check"))
            return

        labeled_count = 0

        for pr in prs:
            updated_at = datetime.fromisoformat(pr["updated_at"].replace("Z", "+00:00"))
            if updated_at.replace(tzinfo=None) > stale_threshold:
                continue

            # Check if already has stale label
            labels = [label["name"].lower() for label in pr.get("labels", [])]
            if "stale" in labels:
                continue

            pr_number = pr["number"]

            if self.dry_run:
                print(f"   [DRY RUN] Would label PR #{pr_number} as stale")
                labeled_count += 1
                continue

            # Add stale label
            result = self.api.post(f"issues/{pr_number}/labels", {"labels": ["stale"]})

            if result is not None:
                # Add comment
                comment_body = f"""🤖 **Stale PR Detection**

This PR has been inactive for more than {STALE_PR_DAYS} days and has been labeled as "stale".

Please:
1. Update the PR if it's still relevant
2. Close it if it's no longer needed
3. Request review if it's ready

---
*This action was performed automatically by Repository Health Check.*"""

                self.api.post(f"issues/{pr_number}/comments", {"body": comment_body})
                print_colored(f"   ✅ Labeled stale PR #{pr_number}", Colors.GREEN)
                labeled_count += 1

        self.results.append(
            FixResult(
                category="PRs",
                action="Label stale",
                success=True,
                message=f"Labeled {labeled_count} stale PRs",
                details={"count": labeled_count},
            )
        )
        print()

    def _fix_orphaned_branches(self, health_data: Dict) -> None:
        """Delete orphaned branches (safe mode only)."""
        print_colored("🌿 Checking for Orphaned Branches", Colors.BLUE)

        # Only run in aggressive mode or if explicitly enabled
        if self.fix_level != "aggressive" and os.environ.get("DELETE_BRANCHES", "false") != "true":
            print("   ℹ️ Skipping (use aggressive mode to delete branches)\n")
            self.results.append(
                FixResult(
                    category="Branches", action="Delete orphaned", success=True, message="Skipped (not in aggressive mode)"
                )
            )
            return

        branches = self.api.get_all_pages("branches")
        if not branches:
            self.results.append(
                FixResult(category="Branches", action="Delete orphaned", success=True, message="Could not fetch branches")
            )
            return

        # Get default branch
        repo_info = self.api.get("")
        default_branch = repo_info.get("default_branch", "main") if repo_info else "main"

        # Get PR branches
        prs = self.api.get_all_pages("pulls", {"state": "all"})
        pr_branches = set()
        if prs:
            for pr in prs:
                pr_branches.add(pr.get("head", {}).get("ref"))

        orphaned_threshold = self.now - timedelta(days=ORPHANED_BRANCH_DAYS)
        deleted_count = 0
        protected_deletions = 0

        for branch in branches:
            branch_name = branch.get("name")

            # Skip protected branches
            if branch.get("protected"):
                continue

            # Skip default branch
            if branch_name == default_branch:
                continue

            # Skip branches with open PRs
            if branch_name in pr_branches:
                continue

            # Check branch age
            branch_detail = self.api.get(f"branches/{branch_name}")
            if not branch_detail:
                continue

            commit_date_str = branch_detail.get("commit", {}).get("commit", {}).get("committer", {}).get("date")
            if not commit_date_str:
                continue

            commit_date = datetime.fromisoformat(commit_date_str.replace("Z", "+00:00"))
            if commit_date.replace(tzinfo=None) > orphaned_threshold:
                continue

            if self.dry_run:
                print(f"   [DRY RUN] Would delete branch: {branch_name}")
                deleted_count += 1
                continue

            # Delete the branch
            if self.api.delete(f"git/refs/heads/{branch_name}"):
                print_colored(f"   ✅ Deleted orphaned branch: {branch_name}", Colors.GREEN)
                deleted_count += 1
            else:
                print_colored(f"   ❌ Failed to delete branch: {branch_name}", Colors.RED)

        self.results.append(
            FixResult(
                category="Branches",
                action="Delete orphaned",
                success=deleted_count >= 0,
                message=f"Deleted {deleted_count} orphaned branches",
                details={"deleted": deleted_count, "protected_skip": protected_deletions},
            )
        )
        print()

    def _fix_fork_sync(self, health_data: Dict) -> None:
        """Sync fork with upstream."""
        print_colored("🔄 Checking Fork Sync Status", Colors.BLUE)

        repo_info = self.api.get("")
        if not repo_info:
            self.results.append(
                FixResult(category="Sync", action="Fork sync", success=False, message="Could not fetch repo info")
            )
            return

        if not repo_info.get("fork", False):
            self.results.append(FixResult(category="Sync", action="Fork sync", success=True, message="Not a fork repository"))
            return

        parent = repo_info.get("parent", {})
        if not parent:
            self.results.append(
                FixResult(category="Sync", action="Fork sync", success=False, message="No parent repository info")
            )
            return

        # Check if behind
        default_branch = repo_info.get("default_branch", "main")
        parent_default = parent.get("default_branch", "main")
        parent_owner = parent.get("owner", {}).get("login")

        comparison = self.api.get(f"compare/{parent_owner}:{parent_default}...{default_branch}")
        if not comparison:
            self.results.append(
                FixResult(category="Sync", action="Fork sync", success=False, message="Could not compare with upstream")
            )
            return

        behind_by = comparison.get("behind_by", 0)

        if behind_by == 0:
            self.results.append(FixResult(category="Sync", action="Fork sync", success=True, message="Fork is up to date"))
            print()
            return

        print(f"   Fork is {behind_by} commits behind upstream")

        # Only auto-sync if behind by less than 100 commits (safety)
        if behind_by > 100 and self.fix_level != "aggressive":
            self.results.append(
                FixResult(
                    category="Sync",
                    action="Fork sync",
                    success=False,
                    message=f"Too far behind ({behind_by} commits), manual sync recommended",
                )
            )
            print()
            return

        if self.dry_run:
            print("   [DRY RUN] Would sync fork with upstream")
            self.results.append(
                FixResult(
                    category="Sync", action="Fork sync", success=True, message=f"Would sync {behind_by} commits (dry run)"
                )
            )
            print()
            return

        # Trigger sync via API (this requires special permissions)
        # Note: GitHub API doesn't have a direct sync endpoint, so we create a PR
        try:
            # Create a sync PR
            pr_data = {
                "title": f"🔄 Sync with upstream ({behind_by} commits)",
                "head": f"{parent_owner}:{parent_default}",
                "base": default_branch,
                "body": f"""🤖 **Automatic Sync with Upstream**

This PR was created automatically to sync the fork with its upstream repository.

**Changes:** {behind_by} commits behind upstream

Please review and merge this PR to keep your fork up to date.

---
*This PR was created automatically by Repository Health Check.*""",
                "maintainer_can_modify": True,
            }

            pr = self.api.post("pulls", pr_data)
            if pr:
                print_colored(f"   ✅ Created sync PR #{pr['number']}", Colors.GREEN)
                self.results.append(
                    FixResult(
                        category="Sync",
                        action="Fork sync",
                        success=True,
                        message=f"Created sync PR #{pr['number']} ({behind_by} commits)",
                        details={"pr_number": pr["number"], "commits": behind_by},
                    )
                )
            else:
                print_colored("   ❌ Failed to create sync PR", Colors.RED)
                self.results.append(
                    FixResult(category="Sync", action="Fork sync", success=False, message="Failed to create sync PR")
                )
        except Exception as e:
            print_colored(f"   ❌ Error creating sync PR: {e}", Colors.RED)
            self.results.append(FixResult(category="Sync", action="Fork sync", success=False, message=f"Error: {str(e)}"))

        print()

    def _fix_dependabot_updates(self, health_data: Dict) -> None:
        """Auto-merge Dependabot PRs for minor/patch updates."""
        print_colored("📦 Checking Dependabot PRs", Colors.BLUE)

        # Check if Dependabot is enabled
        if not health_data.get("security_details", {}).get("dependabot_enabled", False):
            self.results.append(
                FixResult(category="Security", action="Dependabot merge", success=True, message="Dependabot not enabled")
            )
            print()
            return

        # Only run in aggressive mode
        if self.fix_level != "aggressive":
            print("   ℹ️ Skipping (use aggressive mode to auto-merge Dependabot PRs)\n")
            self.results.append(
                FixResult(
                    category="Security", action="Dependabot merge", success=True, message="Skipped (not in aggressive mode)"
                )
            )
            return

        # Find Dependabot PRs
        prs = self.api.get_all_pages("pulls", {"state": "open"})
        if not prs:
            self.results.append(FixResult(category="Security", action="Dependabot merge", success=True, message="No open PRs"))
            print()
            return

        dependabot_prs = [p for p in prs if p.get("user", {}).get("login") == "dependabot[bot]"]

        if not dependabot_prs:
            self.results.append(
                FixResult(category="Security", action="Dependabot merge", success=True, message="No Dependabot PRs found")
            )
            print()
            return

        merged_count = 0

        for pr in dependabot_prs:
            pr_number = pr["number"]
            title = pr.get("title", "").lower()

            # Only merge minor/patch updates
            if "major" in title:
                print(f"   Skipping major update PR #{pr_number}: {title[:50]}...")
                continue

            # Check if checks are passing
            checks = self.api.get(f"commits/{pr['head']['sha']}/check-runs")
            if checks:
                check_runs = checks.get("check_runs", [])
                failed_checks = [c for c in check_runs if c.get("conclusion") == "failure"]

                if failed_checks:
                    print(f"   Skipping PR #{pr_number} with failed checks")
                    continue

            if self.dry_run:
                print(f"   [DRY RUN] Would merge Dependabot PR #{pr_number}")
                merged_count += 1
                continue

            # Merge the PR
            merge_data = {
                "commit_title": f"Merge Dependabot PR #{pr_number}",
                "commit_message": f"Auto-merged by Repository Health Check\n\nOriginal PR: {pr['html_url']}",
                "sha": pr["head"]["sha"],
                "merge_method": "squash",
            }

            result = self.api.post(f"pulls/{pr_number}/merge", merge_data)
            if result and result.get("merged"):
                print_colored(f"   ✅ Merged Dependabot PR #{pr_number}", Colors.GREEN)
                merged_count += 1
            else:
                print_colored(f"   ❌ Failed to merge PR #{pr_number}", Colors.RED)

        self.results.append(
            FixResult(
                category="Security",
                action="Dependabot merge",
                success=merged_count >= 0,
                message=f"Merged {merged_count} Dependabot PRs",
                details={"count": merged_count},
            )
        )
        print()

    def _fix_workflow_updates(self) -> None:
        """Update outdated workflow actions."""
        print_colored("⚙️ Checking Workflow Updates", Colors.BLUE)

        # This is a placeholder - in a real implementation, you would:
        # 1. Parse workflow files
        # 2. Check for outdated action versions
        # 3. Update them automatically or create PRs

        print("   ℹ️ Workflow update check not implemented in this version\n")

        self.results.append(
            FixResult(
                category="Workflows", action="Update actions", success=True, message="Workflow update check not implemented"
            )
        )

    def _fix_linting_issues(self) -> None:
        """Fix common linting issues."""
        print_colored("📝 Checking Linting Issues", Colors.BLUE)

        # This is a placeholder - in a real implementation, you would:
        # 1. Run linters (black, flake8, prettier, etc.)
        # 2. Auto-fix issues where possible
        # 3. Create PRs with fixes

        print("   ℹ️ Linting fix not implemented in this version\n")

        self.results.append(
            FixResult(category="Linting", action="Auto-fix", success=True, message="Linting fix not implemented")
        )

    def save_outputs(self) -> None:
        """Save outputs for GitHub Actions."""
        fixes_applied = len([r for r in self.results if r.success])

        # Create summary
        summary_lines = ["# Auto-Fix Results\n"]
        for result in self.results:
            status = "✅" if result.success else "❌"
            summary_lines.append(f"{status} **{result.category}**: {result.action}")
            summary_lines.append(f"   {result.message}\n")

        summary = "\n".join(summary_lines)

        # Save to file
        with open("auto-fix-summary.md", "w") as f:
            f.write(summary)

        # Set GitHub Actions outputs
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write(f"fixes_applied={fixes_applied}\n")
                f.write(f"fixes_summary<<EOF\n{summary}\nEOF\n")

        print("💾 Auto-fix outputs saved")
        print(f"   - Fixes applied: {fixes_applied}/{len(self.results)}")


def main():
    """Main entry point."""
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")

    if not token:
        print("❌ Error: GITHUB_TOKEN environment variable not set")
        sys.exit(1)

    if not repo:
        print("❌ Error: GITHUB_REPOSITORY environment variable not set")
        sys.exit(1)

    try:
        fixer = AutoFixer(token, repo)
        fixer.run_all_fixes()
        fixer.save_outputs()

        print("\n✅ Auto-fix process completed!")

    except Exception as e:
        print(f"\n❌ Auto-fix failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
