#!/usr/bin/env python3
"""
Zen AI Pentest - Automatic Changelog Generator

This script automatically generates a changelog from git commits and GitHub issues/PRs.

Usage:
    python generate_changelog.py [--version VERSION] [--output FILE]

Examples:
    python generate_changelog.py --version v1.2.0
    python generate_changelog.py --version v1.2.0 --output CHANGELOG.md
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class ChangelogGenerator:
    """Generate changelog from git history and GitHub data."""

    # Conventional commit types
    COMMIT_TYPES = {
        "feat": "✨ Features",
        "fix": "🐛 Bug Fixes",
        "docs": "📖 Documentation",
        "style": "💎 Styles",
        "refactor": "♻️ Code Refactoring",
        "perf": "⚡ Performance",
        "test": "✅ Tests",
        "chore": "🔧 Chores",
        "ci": "👷 CI/CD",
        "security": "🔒 Security",
        "deps": "📦 Dependencies",
    }

    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self.github_token = os.environ.get("GITHUB_TOKEN")

    def run_git_command(self, command: List[str]) -> str:
        """Run a git command and return the output."""
        try:
            result = subprocess.run(
                ["git"] + command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {e}", file=sys.stderr)
            return ""

    def get_last_tag(self) -> Optional[str]:
        """Get the most recent git tag."""
        result = self.run_git_command(["describe", "--tags", "--abbrev=0"])
        return result if result else None

    def get_commits_since(self, since_tag: Optional[str] = None) -> List[Dict]:
        """Get commits since the given tag or all commits."""
        if since_tag:
            range_spec = f"{since_tag}..HEAD"
        else:
            range_spec = "HEAD"

        # Format: hash|date|author|message
        log_format = "%H|%aI|%an|%s"
        output = self.run_git_command(
            ["log", range_spec, f"--format={log_format}", "--no-merges"]
        )

        commits = []
        for line in output.split("\n"):
            if not line:
                continue
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append(
                    {
                        "hash": parts[0][:7],
                        "date": parts[1],
                        "author": parts[2],
                        "message": parts[3],
                    }
                )

        return commits

    def parse_conventional_commit(self, message: str) -> Tuple[str, str, str]:
        """
        Parse a conventional commit message.
        Returns: (type, scope, description)
        """
        # Pattern: type(scope): description or type: description
        pattern = r"^(\w+)(?:\(([^)]+)\))?: (.+)$"
        match = re.match(pattern, message)

        if match:
            commit_type = match.group(1).lower()
            scope = match.group(2) or ""
            description = match.group(3)
            return commit_type, scope, description

        # If not conventional commit, treat as "other"
        return "other", "", message

    def categorize_commits(self, commits: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize commits by type."""
        categorized = {key: [] for key in self.COMMIT_TYPES.keys()}
        categorized["other"] = []

        for commit in commits:
            commit_type, scope, description = self.parse_conventional_commit(
                commit["message"]
            )

            if commit_type in categorized:
                categorized[commit_type].append(
                    {
                        **commit,
                        "scope": scope,
                        "description": description,
                    }
                )
            else:
                categorized["other"].append(
                    {
                        **commit,
                        "scope": scope,
                        "description": description,
                    }
                )

        return categorized

    def get_contributors(self, commits: List[Dict]) -> List[str]:
        """Get unique contributors from commits."""
        contributors = set()
        for commit in commits:
            contributors.add(commit["author"])
        return sorted(list(contributors))

    def get_stats(self, commits: List[Dict]) -> Dict:
        """Get statistics for the release."""
        # Count files changed, insertions, deletions
        stats_output = self.run_git_command(
            ["diff", "--stat", f"{self.get_last_tag()}..HEAD"]
        )

        files_changed = 0
        insertions = 0
        deletions = 0

        # Parse the stats output
        if stats_output:
            lines = stats_output.split("\n")
            if lines:
                # Last line contains summary
                summary_line = lines[-1]
                numbers = re.findall(r"(\d+)", summary_line)
                if len(numbers) >= 3:
                    files_changed = int(numbers[0])
                    insertions = int(numbers[1])
                    deletions = int(numbers[2])

        return {
            "commits": len(commits),
            "contributors": len(self.get_contributors(commits)),
            "files_changed": files_changed,
            "insertions": insertions,
            "deletions": deletions,
        }

    def generate_changelog(
        self, version: str, since_tag: Optional[str] = None
    ) -> str:
        """Generate the changelog content."""
        today = datetime.now().strftime("%Y-%m-%d")
        commits = self.get_commits_since(since_tag)

        if not commits:
            return (
                f"## [{version}] - {today}\n\nNo changes since last release.\n"
            )

        categorized = self.categorize_commits(commits)
        contributors = self.get_contributors(commits)
        stats = self.get_stats(commits)

        lines = [
            f"## [{version}] - {today}",
            "",
            f"🎉 **{stats['commits']} commits** by **{stats['contributors']} contributors**",
            "",
            f"📊 **Stats:** {stats['files_changed']} files changed, +{stats['insertions']}/-{stats['deletions']}",
            "",
        ]

        # Add categorized sections
        for commit_type, title in self.COMMIT_TYPES.items():
            items = categorized.get(commit_type, [])
            if items:
                lines.append(f"### {title}")
                lines.append("")
                for item in items:
                    scope = f"**{item['scope']}:** " if item["scope"] else ""
                    lines.append(
                        f"- {scope}{item['description']} ({item['hash']})"
                    )
                lines.append("")

        # Add other commits
        if categorized.get("other"):
            lines.append("### 📝 Other Changes")
            lines.append("")
            for item in categorized["other"]:
                lines.append(f"- {item['description']} ({item['hash']})")
            lines.append("")

        # Add contributors section
        if contributors:
            lines.append("### 👥 Contributors")
            lines.append("")
            lines.append(", ".join([f"@{c}" for c in contributors]))
            lines.append("")

        lines.append("---")
        lines.append("")

        return "\n".join(lines)

    def update_changelog_file(
        self, new_content: str, output_file: str = "CHANGELOG.md"
    ):
        """Update the changelog file with new content."""
        existing_content = ""

        if os.path.exists(output_file):
            with open(output_file, "r", encoding="utf-8") as f:
                existing_content = f.read()

        # Check if we need to add header
        if not existing_content.startswith("# Changelog"):
            header = [
                "# Changelog",
                "",
                "All notable changes to Zen AI Pentest will be documented in this file.",
                "",
                "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)",
                "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).",
                "",
                "---",
                "",
            ]
            existing_content = "\n".join(header) + existing_content

        # Insert new content after header
        lines = existing_content.split("\n")
        header_end = 0
        for i, line in enumerate(lines):
            if line.startswith("---"):
                header_end = i + 1
                break

        new_lines = (
            lines[:header_end]
            + [""]
            + new_content.split("\n")
            + lines[header_end:]
        )

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines))

        print(f"✅ Changelog updated: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate changelog for Zen AI Pentest"
    )
    parser.add_argument(
        "--version",
        type=str,
        default=None,
        help="Version number (e.g., v1.2.0)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="CHANGELOG.md",
        help="Output file path",
    )
    parser.add_argument(
        "--since",
        type=str,
        default=None,
        help="Generate changelog since this tag",
    )
    parser.add_argument(
        "--print",
        action="store_true",
        help="Print to stdout instead of writing to file",
    )

    args = parser.parse_args()

    # Auto-detect version from git if not provided
    if not args.version:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            current = result.stdout.strip()
            # Bump minor version
            parts = current.lstrip("v").split(".")
            parts[-1] = str(int(parts[-1]) + 1)
            args.version = f"v{'.'.join(parts)}"
        else:
            args.version = "v0.1.0"

    generator = ChangelogGenerator()

    # Determine since tag
    since_tag = args.since
    if not since_tag:
        since_tag = generator.get_last_tag()

    print(f"📝 Generating changelog for {args.version}...")
    if since_tag:
        print(f"   Comparing against: {since_tag}")

    changelog = generator.generate_changelog(args.version, since_tag)

    if args.print:
        print("\n" + "=" * 60)
        print(changelog)
        print("=" * 60)
    else:
        generator.update_changelog_file(changelog, args.output)
        print(f"✨ Done! Version: {args.version}")


if __name__ == "__main__":
    main()
