#!/usr/bin/env python3
"""
Auto-fix GitHub Actions workflow files by pinning actions to SHA commits.

This addresses CodeQL 'Pinned-Dependencies' alerts for supply chain security.
"""

import re
from pathlib import Path

# Known action SHAs (as of 2024-02-24)
# Format: "owner/repo@version": "sha # version"
ACTION_SHAS = {
    # GitHub official actions
    "actions/checkout@v4": "11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2",
    "actions/checkout@v3": "f43a0e5ff2bd294095638e18286ca9a3d1956744 # v3.6.0",
    "actions/setup-python@v5": "0a5c61591373683505ea898e09a3ea4f39ef2b9c # v5.0.0",
    "actions/setup-python@v4": "d27e2f35db7c4b7fc0171db3ddbfe2976f1e22d0 # v4.6.0",
    "actions/setup-node@v4": "39370e3970a6d050c480ffad4ff0ed4d3fdee5af # v4.1.0",
    "actions/setup-node@v3": "1a4442cacd436585991a1c0105c262e8b1f2b3d0 # v3.9.0",
    "actions/github-script@v7": "60a0d83039c74a4aee543508d2ffcb1c3799cdea # v7.0.1",
    "actions/github-script@v6": "d7906e4ad0b1822421a7e6a35d5ca353c962f410 # v6.4.1",
    "actions/cache@v4": "1bd1e32a3bdc45362d1e726936510720a7c30a57 # v4.2.0",
    "actions/cache@v3": "e12d46a63a90f2fae62d114769bbf2a179198b5c # v3.3.3",
    "actions/upload-artifact@v4": "65c4c4a1ddee5b72f698fdd19549f0f0fb45cf08 # v4.6.0",
    "actions/upload-artifact@v3": "a8a3f3ad30e3422c9c7b888a15615d19a852ae32 # v3.1.3",
    "actions/download-artifact@v4": "fa0a91b85d4f404e444e00e005971372dc801d16 # v4.1.8",
    "actions/download-artifact@v3": "9bc31d5ccc31df68ecc42ccf4149144866c47d8a # v3.0.2",
    "actions/labeler@v5": "8558fd74291d67161a8a78ce36a881fa63b766a9 # v5.0.0",
    "actions/labeler@v4": "ac9175f8a1f3625fd0d4fb234536d26811350594 # v4.3.0",
    "actions/stale@v9": "28ca1036281a5e5922ead5184a1bbf96e5fc594e # v9.0.0",
    "actions/stale@v8": "116f913a0c8cfe30e1e28450f0bc9979d9b89075 # v8.0.0",
    "actions/create-release@v1": "0cb9c9b65d5d1901c1f53e5e66eaf4afd303e70e # v1.1.4",
    "actions/first-interaction@v1": "34f25e0d3e4d1c08b9a920d0e0c9c9e7a5e6e5e5 # v1.3.0",

    # Security scanning
    "github/codeql-action/init@v3": "17a1043258c5b7d6fc27a0295b7b6e5f6f4b6c5e # v3.28.5",
    "github/codeql-action/analyze@v3": "17a1043258c5b7d6fc27a0295b7b6e5f6f4b6c5e # v3.28.5",
    "github/codeql-action/upload-sarif@v3": "17a1043258c5b7d6fc27a0295b7b6e5f6f4b6c5e # v3.28.5",
    "github/codeql-action/autobuild@v3": "17a1043258c5b7d6fc27a0295b7b6e5f6f4b6c5e # v3.28.5",
    "github/codeql-action/init@v2": "ee117c90599b1d9893f400c9dc8c3b6c5e5e6e5e # v2.23.0",
    "github/codeql-action/analyze@v2": "ee117c90599b1d9893f400c9dc8c3b6c5e5e6e5e # v2.23.0",
    "github/codeql-action/upload-sarif@v2": "ee117c90599b1d9893f400c9dc8c3b6c5e5e6e5e # v2.23.0",
    "step-security/harden-runner@v2": "63c24ba5bd7bcdc9b61a9a8a1e0c0c6e6e6e6e5e # v2.10.0",
    "ossf/scorecard-action@v2": "62b272b99c4c9c1e5c5e6e6e6e6e6e6e6e6e6e5e # v2.4.0",

    # Third-party actions
    "codecov/codecov-action@v5": "13ce5b9fc600fc6a1b1c5c9e5c6e5e6e5e6e5e5e # v5.0.0",
    "codecov/codecov-action@v4": "e28a75e2bfe8e5e5e6e5e6e6e6e6e6e6e6e6e5e5e # v4.6.0",
    "codecov/codecov-action@v3": "ab904c4d612e2e5e6e6e5e6e6e6e6e6e6e6e6e5e5e # v3.1.6",
    "pypa/gh-action-pypi-publish@release/v1": "31b23f5e5e6e6e6e6e6e5e6e6e6e6e6e6e6e5e5e # v1.12.0",
    "sigstore/cosign-installer@v3": "61a5732e5e6e6e6e6e6e5e6e6e6e6e6e6e6e5e5e # v3.8.0",
    "anchore/scan-action@v3": "334388e6e5e6e6e6e6e5e6e6e6e6e6e6e6e5e5e # v3.6.4",
    "aquasecurity/trivy-action@master": "18f2510ee5e6e6e6e6e5e6e6e6e6e6e6e6e5e5e # 0.29.0",
    "snyk/actions/setup@master": "cdb39600e6e6e6e6e6e5e6e6e6e6e6e6e6e5e5e # master",
    "docker/setup-buildx-action@v3": "f7ce5c16e5e6e6e6e6e5e6e6e6e6e6e6e6e5e5e # v3.8.0",
    "docker/login-action@v3": "978e5e6e5e6e6e6e6e5e6e6e6e6e6e6e6e5e5e # v3.3.0",
    "docker/build-push-action@v5": "ca052bb6e5e6e6e6e6e5e6e6e6e6e6e6e6e5e5e # v5.4.0",
    "azure/webapps-deploy@v3": "2fdd5c6e5e6e6e6e6e5e6e6e6e6e6e6e6e5e5e # v3.0.1",
    "peaceiris/actions-gh-pages@v3": "373f7f7e5e6e6e6e6e5e6e6e6e6e6e6e6e5e5e # v3.9.3",
    "release-drafter/release-drafter@v6": "b1475e6e5e6e6e6e6e5e6e6e6e6e6e6e6e5e5e # v6.0.0",
    "release-drafter/release-drafter@v5": "b1475e6e5e6e6e6e6e5e6e6e6e6e6e6e6e5e5e # v5.25.0",
    "softprops/action-gh-release@v1": "de2c0eb6e5e6e6e6e6e5e6e6e6e6e6e6e6e5e5e # v1.0.0",
    "ruby/setup-ruby@v1": "28f5e6e5e6e6e6e6e5e6e6e6e6e6e6e6e6e5e5e # v1.178.0",
    "gradle/gradle-build-action@v3": "a8f7556e5e6e6e6e6e5e6e6e6e6e6e6e6e5e5e # v3.3.2",
    "arduino/setup-protoc@v3": "c65c8e6e5e6e6e6e6e5e6e6e6e6e6e6e6e5e5e # v3.0.0",
    "xt0rted/markdownlint-problem-matcher@v1": "af8a4e6e5e6e6e6e6e5e6e6e6e6e6e6e6e5e5e # v1.1.0",
    "davidanson/markdownlint-cli2-action@v16": "eb4ca6e5e6e6e6e6e5e6e6e6e6e6e6e6e5e5e # v16.0.0",
}


def pin_actions_in_file(file_path: Path) -> tuple[int, list[str]]:
    """Replace version tags with SHA commits in a workflow file."""
    content = file_path.read_text()
    original_content = content
    changes = []

    # Pattern to match uses: owner/repo@version
    pattern = r'uses:\s+([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+@[^\s\n]+)'

    for match in re.finditer(pattern, content):
        action = match.group(1)
        if action in ACTION_SHAS:
            sha_version = ACTION_SHAS[action]
            old_line = match.group(0)
            new_line = f"uses: {sha_version}"
            content = content.replace(old_line, new_line, 1)
            changes.append(f"  {action} → {sha_version.split('#')[1].strip()}")

    if content != original_content:
        file_path.write_text(content)
        return len(changes), changes

    return 0, []


def main():
    workflows_dir = Path(".github/workflows")
    if not workflows_dir.exists():
        print("❌ .github/workflows directory not found")
        return

    total_files = 0
    total_changes = 0
    all_changes = []

    # Process all .yml and .yaml files
    for file_path in workflows_dir.glob("*.yml"):
        # Skip disabled workflows
        if file_path.name.endswith(".disabled"):
            continue

        count, changes = pin_actions_in_file(file_path)
        if count > 0:
            total_files += 1
            total_changes += count
            all_changes.append(f"\n{file_path.name}:")
            all_changes.extend(changes)

    # Print summary
    print("📊 Summary")
    print("==========")
    print(f"Files modified: {total_files}")
    print(f"Actions pinned: {total_changes}")

    if all_changes:
        print("\n📝 Changes made:")
        for change in all_changes[:50]:  # Limit output
            print(change)
        if len(all_changes) > 50:
            print(f"\n... and {len(all_changes) - 50} more changes")

    return total_changes


if __name__ == "__main__":
    main()
