#!/usr/bin/env python3
"""
Repository Health Check Script

This script analyzes various aspects of a GitHub repository and calculates
a comprehensive health score based on multiple metrics.

Metrics:
- Issues (status, staleness)
- Pull Requests (status, conflicts, staleness)
- Branches (orphaned, stale)
- Actions (success rate, failures)
- Security (Dependabot, CodeQL)
- Repository sync status
"""

import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests

# Constants
STALE_ISSUE_DAYS = 90
STALE_PR_DAYS = 60
ORPHANED_BRANCH_DAYS = 30
GITHUB_API_URL = "https://api.github.com"


@dataclass
class HealthMetrics:
    """Container for all health metrics."""

    issues_score: float = 0.0
    prs_score: float = 0.0
    branches_score: float = 0.0
    actions_score: float = 0.0
    security_score: float = 0.0
    sync_score: float = 0.0
    overall_score: float = 0.0

    issues_details: Dict[str, Any] = None
    prs_details: Dict[str, Any] = None
    branches_details: Dict[str, Any] = None
    actions_details: Dict[str, Any] = None
    security_details: Dict[str, Any] = None
    sync_details: Dict[str, Any] = None

    recommendations: List[str] = None
    critical_issues: int = 0


class GitHubAPI:
    """GitHub API client with rate limiting and error handling."""

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
        """Make a GET request to the GitHub API."""
        url = urljoin(self.base_url + "/", endpoint)
        try:
            response = requests.get(
                url, headers=self.headers, params=params, timeout=30
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                print(f"⚠️ API Error: {response.status_code} for {url}")
                print(f"   Response: {response.text[:200]}")
                return None
        except Exception as e:
            print(f"⚠️ Request failed: {e}")
            return None

    def get_all_pages(self, endpoint: str, params: Dict = None) -> List[Dict]:
        """Get all pages of results from a paginated endpoint."""
        results = []
        params = params or {}
        params["per_page"] = 100
        page = 1

        while True:
            params["page"] = page
            url = urljoin(self.base_url + "/", endpoint)
            try:
                response = requests.get(
                    url, headers=self.headers, params=params, timeout=30
                )
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

                # Safety limit
                if page > 10:
                    break

            except Exception as e:
                print(f"⚠️ Pagination error: {e}")
                break

        return results


class HealthAnalyzer:
    """Main health analysis class."""

    def __init__(self, token: str, repo: str):
        self.api = GitHubAPI(token, repo)
        self.repo = repo
        self.metrics = HealthMetrics()
        self.metrics.issues_details = {}
        self.metrics.prs_details = {}
        self.metrics.branches_details = {}
        self.metrics.actions_details = {}
        self.metrics.security_details = {}
        self.metrics.sync_details = {}
        self.metrics.recommendations = []

        self.now = datetime.now()
        self.stale_date = self.now - timedelta(days=STALE_ISSUE_DAYS)
        self.stale_pr_date = self.now - timedelta(days=STALE_PR_DAYS)
        self.orphaned_date = self.now - timedelta(days=ORPHANED_BRANCH_DAYS)

    def analyze(self) -> HealthMetrics:
        """Run all health analyses."""
        print("🔍 Starting Repository Health Analysis")
        print(f"   Repository: {self.repo}")
        print(f"   Time: {self.now.isoformat()}")
        print()

        # Run individual analyses
        self._analyze_issues()
        self._analyze_prs()
        self._analyze_branches()
        self._analyze_actions()
        self._analyze_security()
        self._analyze_sync()

        # Calculate overall score
        self._calculate_overall_score()

        # Generate recommendations
        self._generate_recommendations()

        return self.metrics

    def _analyze_issues(self) -> None:
        """Analyze repository issues."""
        print("📋 Analyzing Issues...")

        issues = self.api.get_all_pages("issues", {"state": "all"})

        if issues is None:
            self.metrics.issues_score = 50.0
            self.metrics.issues_details = {"error": "Could not fetch issues"}
            return

        open_issues = [
            i
            for i in issues
            if i.get("state") == "open" and "pull_request" not in i
        ]
        closed_issues = [
            i
            for i in issues
            if i.get("state") == "closed" and "pull_request" not in i
        ]

        stale_issues = []
        for issue in open_issues:
            updated_at = datetime.fromisoformat(
                issue["updated_at"].replace("Z", "+00:00")
            )
            if updated_at.replace(tzinfo=None) < self.stale_date:
                stale_issues.append(issue)

        # Calculate score
        total_issues = len(open_issues) + len(closed_issues)
        if total_issues == 0:
            self.metrics.issues_score = 100.0
        else:
            open_ratio = len(open_issues) / total_issues
            stale_ratio = len(stale_issues) / max(len(open_issues), 1)

            # Score based on open ratio and stale issues
            self.metrics.issues_score = max(
                0, 100 - (open_ratio * 30) - (stale_ratio * 40)
            )

        self.metrics.issues_details = {
            "total": total_issues,
            "open": len(open_issues),
            "closed": len(closed_issues),
            "stale": len(stale_issues),
            "stale_threshold_days": STALE_ISSUE_DAYS,
        }

        # Count critical issues
        critical_labels = ["critical", "security", "bug", "crash", "error"]
        critical_count = sum(
            1
            for i in open_issues
            if any(
                label["name"].lower() in critical_labels
                for label in i.get("labels", [])
            )
        )
        self.metrics.critical_issues += critical_count

        print(
            f"   ✓ Issues: {len(open_issues)} open, {len(stale_issues)} stale, score: {self.metrics.issues_score:.1f}"
        )

    def _analyze_prs(self) -> None:
        """Analyze pull requests."""
        print("🔀 Analyzing Pull Requests...")

        prs = self.api.get_all_pages("pulls", {"state": "all"})

        if prs is None:
            self.metrics.prs_score = 50.0
            self.metrics.prs_details = {"error": "Could not fetch PRs"}
            return

        open_prs = [p for p in prs if p.get("state") == "open"]
        closed_prs = [p for p in prs if p.get("state") == "closed"]

        # Check for stale PRs
        stale_prs = []
        conflict_prs = []

        for pr in open_prs:
            updated_at = datetime.fromisoformat(
                pr["updated_at"].replace("Z", "+00:00")
            )
            if updated_at.replace(tzinfo=None) < self.stale_pr_date:
                stale_prs.append(pr)

            # Check for merge conflicts
            if pr.get("mergeable") is False:
                conflict_prs.append(pr)

        # Calculate score
        total_prs = len(open_prs) + len(closed_prs)
        if total_prs == 0:
            self.metrics.prs_score = 100.0
        else:
            open_ratio = len(open_prs) / total_prs
            stale_ratio = len(stale_prs) / max(len(open_prs), 1)
            conflict_ratio = len(conflict_prs) / max(len(open_prs), 1)

            self.metrics.prs_score = max(
                0,
                100
                - (open_ratio * 20)
                - (stale_ratio * 30)
                - (conflict_ratio * 50),
            )

        self.metrics.prs_details = {
            "total": total_prs,
            "open": len(open_prs),
            "closed": len(closed_prs),
            "stale": len(stale_prs),
            "conflicts": len(conflict_prs),
            "stale_threshold_days": STALE_PR_DAYS,
        }

        print(
            f"   ✓ PRs: {len(open_prs)} open, {len(stale_prs)} stale, "
            f"{len(conflict_prs)} conflicts, score: {self.metrics.prs_score:.1f}"
        )

    def _analyze_branches(self) -> None:
        """Analyze repository branches."""
        print("🌿 Analyzing Branches...")

        branches = self.api.get_all_pages("branches")

        if branches is None:
            self.metrics.branches_score = 50.0
            self.metrics.branches_details = {
                "error": "Could not fetch branches"
            }
            return

        # Get default branch
        repo_info = self.api.get("")
        default_branch = (
            repo_info.get("default_branch", "main") if repo_info else "main"
        )

        # Get all PRs to check which branches are associated
        prs = self.api.get_all_pages("pulls", {"state": "all"})
        pr_branches = set()
        if prs:
            for pr in prs:
                pr_branches.add(pr.get("head", {}).get("ref"))
                pr_branches.add(pr.get("base", {}).get("ref"))

        protected_branches = [b for b in branches if b.get("protected")]

        # Check for orphaned branches (branches without PRs, not default, old)
        orphaned_branches = []
        for branch in branches:
            branch_name = branch.get("name")
            if branch_name == default_branch or branch_name in pr_branches:
                continue

            # Get branch details
            branch_detail = self.api.get(f"branches/{branch_name}")
            if branch_detail:
                commit_date_str = (
                    branch_detail.get("commit", {})
                    .get("commit", {})
                    .get("committer", {})
                    .get("date")
                )
                if commit_date_str:
                    commit_date = datetime.fromisoformat(
                        commit_date_str.replace("Z", "+00:00")
                    )
                    if commit_date.replace(tzinfo=None) < self.orphaned_date:
                        orphaned_branches.append(branch_name)

        # Calculate score
        total_branches = len(branches)
        protected_count = len(protected_branches)
        orphaned_count = len(orphaned_branches)

        if total_branches == 0:
            self.metrics.branches_score = 100.0
        else:
            protected_ratio = protected_count / total_branches
            orphaned_ratio = orphaned_count / total_branches

            self.metrics.branches_score = max(
                0, 100 - (orphaned_ratio * 40) + (protected_ratio * 10)
            )

        self.metrics.branches_details = {
            "total": total_branches,
            "protected": protected_count,
            "orphaned": orphaned_count,
            "orphaned_threshold_days": ORPHANED_BRANCH_DAYS,
        }

        print(
            f"   ✓ Branches: {total_branches} total, {protected_count} protected, "
            f"{orphaned_count} orphaned, score: {self.metrics.branches_score:.1f}"
        )

    def _analyze_actions(self) -> None:
        """Analyze GitHub Actions status."""
        print("⚙️ Analyzing GitHub Actions...")

        # Get recent workflow runs
        runs = self.api.get("actions/runs", {"per_page": 100})

        if runs is None or "workflow_runs" not in runs:
            self.metrics.actions_score = 50.0
            self.metrics.actions_details = {
                "error": "Could not fetch workflow runs"
            }
            return

        workflow_runs = runs["workflow_runs"]

        # Filter to last 30 days
        thirty_days_ago = self.now - timedelta(days=30)
        recent_runs = [
            r
            for r in workflow_runs
            if datetime.fromisoformat(
                r["created_at"].replace("Z", "+00:00")
            ).replace(tzinfo=None)
            > thirty_days_ago
        ]

        if not recent_runs:
            self.metrics.actions_score = 75.0  # Neutral if no recent runs
            self.metrics.actions_details = {
                "total_runs": 0,
                "success_rate": 0,
                "message": "No workflow runs in last 30 days",
            }
            return

        successful_runs = [
            r for r in recent_runs if r["conclusion"] == "success"
        ]
        failed_runs = [r for r in recent_runs if r["conclusion"] == "failure"]

        success_rate = len(successful_runs) / len(recent_runs) * 100

        # Calculate score based on success rate
        self.metrics.actions_score = min(
            100, success_rate * 1.2
        )  # Give bonus for high success rate

        self.metrics.actions_details = {
            "total_runs": len(recent_runs),
            "successful": len(successful_runs),
            "failed": len(failed_runs),
            "success_rate": round(success_rate, 2),
        }

        print(
            f"   ✓ Actions: {len(recent_runs)} runs, {success_rate:.1f}% success rate, score: {self.metrics.actions_score:.1f}"
        )

    def _analyze_security(self) -> None:
        """Analyze security status."""
        print("🔒 Analyzing Security...")

        security_score = 100.0
        security_details = {
            "dependabot_enabled": False,
            "codeql_enabled": False,
            "secret_scanning_enabled": False,
            "vulnerabilities": 0,
            "alerts": [],
        }

        # Check Dependabot
        try:
            dependabot = self.api.get("dependabot/alerts", {"state": "open"})
            if dependabot is not None:
                security_details["dependabot_enabled"] = True
                if isinstance(dependabot, list):
                    critical_vulns = [
                        a
                        for a in dependabot
                        if a.get("severity") in ["critical", "high"]
                    ]
                    security_details["vulnerabilities"] = len(dependabot)
                    security_details["critical_vulnerabilities"] = len(
                        critical_vulns
                    )
                    security_score -= len(critical_vulns) * 15
                    security_score -= len(dependabot) * 2
        except Exception as e:
            print(f"   ⚠️ Dependabot check failed: {e}")

        # Check for CodeQL workflow
        workflows = self.api.get("contents/.github/workflows")
        if workflows:
            codeql_files = [
                w for w in workflows if "codeql" in w.get("name", "").lower()
            ]
            security_details["codeql_enabled"] = len(codeql_files) > 0
            if not security_details["codeql_enabled"]:
                security_score -= 10

        # Check repository security settings
        repo_info = self.api.get("")
        if repo_info:
            security_details["private"] = repo_info.get("private", False)
            security_details["archived"] = repo_info.get("archived", False)

            if security_details["archived"]:
                security_score = (
                    50.0  # Archived repos get neutral security score
                )

        self.metrics.security_score = max(0, security_score)
        self.metrics.security_details = security_details

        # Update critical issues count
        self.metrics.critical_issues += security_details.get(
            "critical_vulnerabilities", 0
        )

        print(
            f"   ✓ Security: Dependabot={security_details['dependabot_enabled']}, "
            f"CodeQL={security_details['codeql_enabled']}, "
            f"Vulns={security_details['vulnerabilities']}, "
            f"score: {self.metrics.security_score:.1f}"
        )

    def _analyze_sync(self) -> None:
        """Analyze repository sync status (forks)."""
        print("🔄 Analyzing Sync Status...")

        repo_info = self.api.get("")

        if not repo_info:
            self.metrics.sync_score = 50.0
            self.metrics.sync_details = {"error": "Could not fetch repo info"}
            return

        is_fork = repo_info.get("fork", False)

        if not is_fork:
            self.metrics.sync_score = 100.0
            self.metrics.sync_details = {
                "is_fork": False,
                "message": "Not a fork repository",
            }
            print(
                f"   ✓ Sync: Not a fork, score: {self.metrics.sync_score:.1f}"
            )
            return

        # For forks, check if behind upstream
        parent = repo_info.get("parent", {})
        if parent:
            parent_default = parent.get("default_branch", "main")
            comparison = self.api.get(
                f"compare/{parent['owner']['login']}:{parent_default}...{repo_info.get('default_branch', 'main')}"
            )

            if comparison:
                behind_by = comparison.get("behind_by", 0)
                ahead_by = comparison.get("ahead_by", 0)

                # Calculate score based on how far behind
                if behind_by == 0:
                    self.metrics.sync_score = 100.0
                elif behind_by < 10:
                    self.metrics.sync_score = 90.0
                elif behind_by < 50:
                    self.metrics.sync_score = 70.0
                else:
                    self.metrics.sync_score = max(0, 50 - behind_by)

                self.metrics.sync_details = {
                    "is_fork": True,
                    "parent_repo": parent.get("full_name"),
                    "behind_by": behind_by,
                    "ahead_by": ahead_by,
                }
            else:
                self.metrics.sync_score = 75.0
                self.metrics.sync_details = {
                    "is_fork": True,
                    "message": "Could not compare with upstream",
                }
        else:
            self.metrics.sync_score = 75.0
            self.metrics.sync_details = {
                "is_fork": True,
                "message": "No parent repository info",
            }

        print(
            f"   ✓ Sync: Fork, behind by {self.metrics.sync_details.get('behind_by', 'unknown')}, "
            f"score: {self.metrics.sync_score:.1f}"
        )

    def _calculate_overall_score(self) -> None:
        """Calculate the overall health score."""
        # Weights for each component
        weights = {
            "issues": 0.20,
            "prs": 0.10,
            "branches": 0.10,
            "actions": 0.25,
            "security": 0.25,
            "sync": 0.10,
        }

        self.metrics.overall_score = (
            self.metrics.issues_score * weights["issues"]
            + self.metrics.prs_score * weights["prs"]
            + self.metrics.branches_score * weights["branches"]
            + self.metrics.actions_score * weights["actions"]
            + self.metrics.security_score * weights["security"]
            + self.metrics.sync_score * weights["sync"]
        )

        print()
        print(f"📊 Overall Health Score: {self.metrics.overall_score:.1f}/100")

    def _generate_recommendations(self) -> None:
        """Generate actionable recommendations."""
        recommendations = []

        # Issues recommendations
        if self.metrics.issues_details.get("stale", 0) > 5:
            recommendations.append(
                f"📝 Close {self.metrics.issues_details['stale']} stale issues (inactive > {STALE_ISSUE_DAYS} days)"
            )

        if self.metrics.issues_details.get("open", 0) > 50:
            recommendations.append(
                f"📝 Consider triaging {self.metrics.issues_details['open']} open issues"
            )

        # PR recommendations
        if self.metrics.prs_details.get("conflicts", 0) > 0:
            recommendations.append(
                f"🔀 Resolve merge conflicts in {self.metrics.prs_details['conflicts']} PRs"
            )

        if self.metrics.prs_details.get("stale", 0) > 3:
            recommendations.append(
                f"🔀 Review {self.metrics.prs_details['stale']} stale PRs"
            )

        # Branch recommendations
        if self.metrics.branches_details.get("orphaned", 0) > 5:
            recommendations.append(
                f"🌿 Clean up {self.metrics.branches_details['orphaned']} orphaned branches"
            )

        # Actions recommendations
        if self.metrics.actions_details.get("success_rate", 100) < 80:
            success_rate = self.metrics.actions_details.get("success_rate", 0)
            recommendations.append(
                f"⚙️ Investigate workflow failures (current success rate: {success_rate}%)"
            )

        # Security recommendations
        if not self.metrics.security_details.get("dependabot_enabled"):
            recommendations.append(
                "🔒 Enable Dependabot for automated dependency updates"
            )

        if not self.metrics.security_details.get("codeql_enabled"):
            recommendations.append(
                "🔒 Add CodeQL workflow for security analysis"
            )

        if self.metrics.security_details.get("vulnerabilities", 0) > 0:
            recommendations.append(
                f"🔒 Address {self.metrics.security_details['vulnerabilities']} security vulnerabilities"
            )

        # Sync recommendations
        if (
            self.metrics.sync_details.get("is_fork")
            and self.metrics.sync_details.get("behind_by", 0) > 0
        ):
            recommendations.append(
                f"🔄 Sync fork with upstream (behind by {self.metrics.sync_details['behind_by']} commits)"
            )

        self.metrics.recommendations = recommendations

        print(f"💡 Generated {len(recommendations)} recommendations")

    def generate_report(self) -> str:
        """Generate a markdown report."""
        score = self.metrics.overall_score
        status = (
            "🟢 Healthy"
            if score >= 80
            else "🟡 Needs Attention" if score >= 50 else "🔴 Critical"
        )

        report = f"""# Repository Health Report

Generated: {self.now.strftime("%Y-%m-%d %H:%M UTC")}

## Overall Health Score: {score:.1f}/100 {status}

| Component | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| 📋 Issues | {self.metrics.issues_score:.1f} | 20% | {self.metrics.issues_score * 0.2:.1f} |
| 🔀 Pull Requests | {self.metrics.prs_score:.1f} | 10% | {self.metrics.prs_score * 0.1:.1f} |
| 🌿 Branches | {self.metrics.branches_score:.1f} | 10% | {self.metrics.branches_score * 0.1:.1f} |
| ⚙️ Actions | {self.metrics.actions_score:.1f} | 25% | {self.metrics.actions_score * 0.25:.1f} |
| 🔒 Security | {self.metrics.security_score:.1f} | 25% | {self.metrics.security_score * 0.25:.1f} |
| 🔄 Sync | {self.metrics.sync_score:.1f} | 10% | {self.metrics.sync_score * 0.1:.1f} |

---

## 📋 Issues Status

- **Total Issues:** {self.metrics.issues_details.get("total", "N/A")}
- **Open Issues:** {self.metrics.issues_details.get("open", "N/A")}
- **Closed Issues:** {self.metrics.issues_details.get("closed", "N/A")}
- **Stale Issues:** {self.metrics.issues_details.get("stale", "N/A")} (>{STALE_ISSUE_DAYS} days inactive)

---

## 🔀 Pull Requests Status

- **Total PRs:** {self.metrics.prs_details.get("total", "N/A")}
- **Open PRs:** {self.metrics.prs_details.get("open", "N/A")}
- **Stale PRs:** {self.metrics.prs_details.get("stale", "N/A")} (>{STALE_PR_DAYS} days inactive)
- **PRs with Conflicts:** {self.metrics.prs_details.get("conflicts", "N/A")}

---

## 🌿 Branch Status

- **Total Branches:** {self.metrics.branches_details.get("total", "N/A")}
- **Protected Branches:** {self.metrics.branches_details.get("protected", "N/A")}
- **Orphaned Branches:** {self.metrics.branches_details.get("orphaned", "N/A")} (>{ORPHANED_BRANCH_DAYS} days old, no PR)

---

## ⚙️ GitHub Actions Status

- **Recent Runs (30 days):** {self.metrics.actions_details.get("total_runs", "N/A")}
- **Successful:** {self.metrics.actions_details.get("successful", "N/A")}
- **Failed:** {self.metrics.actions_details.get("failed", "N/A")}
- **Success Rate:** {self.metrics.actions_details.get("success_rate", "N/A")}%

---

## 🔒 Security Status

- **Dependabot Enabled:** {"✅ Yes" if self.metrics.security_details.get("dependabot_enabled") else "❌ No"}
- **CodeQL Enabled:** {"✅ Yes" if self.metrics.security_details.get("codeql_enabled") else "❌ No"}
- **Open Vulnerabilities:** {self.metrics.security_details.get("vulnerabilities", "N/A")}
- **Critical Vulnerabilities:** {self.metrics.security_details.get("critical_vulnerabilities", 0)}

---

## 🔄 Sync Status

- **Is Fork:** {"✅ Yes" if self.metrics.sync_details.get("is_fork") else "❌ No"}
"""

        if self.metrics.sync_details.get("is_fork"):
            report += f"""- **Parent Repository:** {self.metrics.sync_details.get("parent_repo", "N/A")}
- **Behind Upstream:** {self.metrics.sync_details.get("behind_by", "N/A")} commits
- **Ahead of Upstream:** {self.metrics.sync_details.get("ahead_by", "N/A")} commits
"""

        report += """
---

## 💡 Recommendations

"""

        if self.metrics.recommendations:
            for i, rec in enumerate(self.metrics.recommendations, 1):
                report += f"{i}. {rec}\n"
        else:
            report += "✅ No recommendations at this time. Repository looks healthy!\n"

        report += """
---

## 📊 Health Score Trend

See `.github/health-trends/` for historical data.

---

*Report generated by Repository Health Check workflow*
"""

        return report

    def save_outputs(self) -> None:
        """Save outputs for GitHub Actions."""
        # Save score
        with open("health-score.txt", "w") as f:
            f.write(str(int(self.metrics.overall_score)))

        # Save report
        with open("health-report.md", "w") as f:
            f.write(self.generate_report())

        # Save JSON data
        with open("health-data.json", "w") as f:
            json.dump(asdict(self.metrics), f, indent=2, default=str)

        # Set GitHub Actions outputs
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write(f"health_score={int(self.metrics.overall_score)}\n")

                status = (
                    "Healthy"
                    if self.metrics.overall_score >= 80
                    else (
                        "Needs Attention"
                        if self.metrics.overall_score >= 50
                        else "Critical"
                    )
                )
                f.write(f"health_status={status}\n")

                f.write("report_file=health-report.md\n")
                f.write(f"critical_issues={self.metrics.critical_issues}\n")
                f.write(
                    f"has_recommendations={'true' if self.metrics.recommendations else 'false'}\n"
                )

        print()
        print("💾 Outputs saved:")
        print("   - health-score.txt")
        print("   - health-report.md")
        print("   - health-data.json")


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
        analyzer = HealthAnalyzer(token, repo)
        analyzer.analyze()
        analyzer.save_outputs()

        # Exit with error code if score is critical
        if analyzer.metrics.overall_score < 30:
            print("\n❌ Critical health score detected!")
            sys.exit(2)

        print("\n✅ Health check completed successfully!")

    except Exception as e:
        print(f"\n❌ Health check failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
