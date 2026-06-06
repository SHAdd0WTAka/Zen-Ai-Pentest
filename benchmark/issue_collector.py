#!/usr/bin/env python3
"""
Zen-AI-Pentest Benchmark Framework
Collects GitHub issues and extracts patches for SWE-bench style evaluation.
"""

import argparse
import json
import os
from pathlib import Path
from typing import Any

import requests


class IssueCollector:
    """Collects GitHub issues and their corresponding patches."""

    def __init__(
        self,
        token: str | None = None,
        owner: str = "SHAdd0WTAka",
        repo: str = "zen-ai-pentest",
    ):
        self.owner = owner
        self.repo = repo
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    def fetch_issues(self, state: str = "all", per_page: int = 100) -> list[dict[str, Any]]:
        """Fetch issues from GitHub."""
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/issues"
        params = {
            "state": state,
            "per_page": per_page,
            "sort": "updated",
            "direction": "desc",
        }

        all_issues = []
        page = 1

        while len(all_issues) < per_page * page:
            params["page"] = page
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            issues = response.json()

            if not issues:
                break

            all_issues.extend(issues)
            page += 1

            if len(all_issues) >= per_page:
                break

        return all_issues

    def fetch_pull_requests(self, state: str = "all", per_page: int = 100) -> list[dict[str, Any]]:
        """Fetch pull requests from GitHub."""
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/pulls"
        params = {
            "state": state,
            "per_page": per_page,
            "sort": "updated",
            "direction": "desc",
        }

        all_prs = []
        page = 1

        while len(all_prs) < per_page * page:
            params["page"] = page
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            prs = response.json()

            if not prs:
                break

            all_prs.extend(prs)
            page += 1

            if len(all_prs) >= per_page:
                break

        return all_prs

    def get_pr_files(self, pr_number: int) -> list[dict[str, Any]]:
        """Get files changed in a PR."""
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/pulls/{pr_number}/files"
        params = {"per_page": 100}

        response = requests.get(url, headers=self.headers, params=params, timeout=30)
        response.raise_for_status()

        return response.json()

    def get_pr_diff(self, pr_number: int) -> str:
        """Get the full diff of a PR."""
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/pulls/{pr_number}"

        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()

        pr = response.json()

        return pr.get("diff_url", "")

    def export_issues(self, output_dir: Path, max_issues: int = 50) -> None:
        """Export issues to JSON files."""
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"Fetching issues from {self.owner}/{self.repo}...")
        issues = self.fetch_issues(per_page=max_issues)

        issue_file = output_dir / "issues.json"
        with open(issue_file, "w") as f:
            json.dump(issues, f, indent=2, default=str)

        print(f"Exported {len(issues)} issues to {issue_file}")

        print(f"Fetching PRs from {self.owner}/{self.repo}...")
        prs = self.fetch_pull_requests(per_page=max_issues)

        pr_file = output_dir / "pull_requests.json"
        with open(pr_file, "w") as f:
            json.dump(prs, f, indent=2, default=str)

        print(f"Exported {len(prs)} PRs to {pr_file}")

    def create_issue_fix_pairs(self, output_dir: Path, max_pairs: int = 20) -> None:
        """Create issue-fix pairs from PRs that close issues."""
        output_dir.mkdir(parents=True, exist_ok=True)

        prs = self.fetch_pull_requests(state="closed", per_page=100)

        pairs = []

        for pr in prs[:max_pairs]:
            pr.get("number")
            title = pr.get("title", "")
            body = pr.get("body", "") or ""
            merged_at = pr.get("merged_at")

            if merged_at:
                pr_num = pr.get("number", 0)
                if pr_num:
                    files = self.get_pr_files(pr_num)

                    pair = {
                        "pr_number": pr_num,
                        "title": title,
                        "description": body[:500] if body else "",
                        "merged_at": merged_at,
                        "files_changed": [f.get("filename") for f in files],
                        "additions": sum(f.get("additions", 0) for f in files),
                        "deletions": sum(f.get("deletions", 0) for f in files),
                    }

                    pairs.append(pair)

        pairs_file = output_dir / "issue_fix_pairs.json"
        with open(pairs_file, "w") as f:
            json.dump(pairs, f, indent=2, default=str)

        print(f"Created {len(pairs)} issue-fix pairs in {pairs_file}")


def main():
    parser = argparse.ArgumentParser(description="Collect GitHub issues for benchmark")
    parser.add_argument("--owner", default="SHAdd0WTAka", help="Repository owner")
    parser.add_argument("--repo", default="zen-ai-pentest", help="Repository name")
    parser.add_argument("--output", default="benchmark/data", help="Output directory")
    parser.add_argument("--max-issues", type=int, default=50, help="Max issues to fetch")
    parser.add_argument(
        "--create-pairs",
        action="store_true",
        help="Create issue-fix pairs from PRs",
    )
    args = parser.parse_args()

    collector = IssueCollector(owner=args.owner, repo=args.repo)
    output_dir = Path(args.output)

    collector.export_issues(output_dir, max_issues=args.max_issues)

    if args.create_pairs:
        collector.create_issue_fix_pairs(output_dir, max_pairs=20)

    print("\nDone! Run evaluation with:")
    print(f"  python -m benchmark.evaluation_runner --data-dir {args.output}")


if __name__ == "__main__":
    main()
