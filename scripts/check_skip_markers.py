#!/usr/bin/env python3
"""
Check for skip/focus markers

Warns about:
- @pytest.mark.skip (without reason)
- @pytest.mark.skipif
- @pytest.mark.xfail
- pytest.skip() calls
- pytest.focus markers
"""

import re
import sys
from pathlib import Path


def check_skip_markers(filepath: str) -> list:
    """Check for problematic skip markers."""
    warnings = []
    content = Path(filepath).read_text()
    lines = content.split("\n")

    # Patterns to check
    patterns = [
        (r"^\s*@pytest\.mark\.skip\s*$", "@pytest.mark.skip without reason"),
        (r"^\s*@pytest\.mark\.skip\([^)]*\)", "@pytest.mark.skip found"),
        (r"^\s*@pytest\.mark\.xfail\s*$", "@pytest.mark.xfail without reason"),
        (r"pytest\.skip\s*\(", "pytest.skip() call"),
        (r"^\s*#.*skip", "Commented skip (might be temporary)"),
        (
            r"@pytest\.mark\.focus",
            "@pytest.mark.focus (should not be committed)",
        ),
    ]

    for i, line in enumerate(lines, 1):
        for pattern, message in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                warnings.append(f"Line {i}: {message}")
                warnings.append(f"  {line.strip()}")

    return warnings


def main():
    """Main entry point."""
    files = sys.argv[1:]

    if not files:
        print("No files to check")
        sys.exit(0)

    all_warnings = []

    for filepath in files:
        if not filepath.endswith(".py"):
            continue

        warnings = check_skip_markers(filepath)
        if warnings:
            all_warnings.append(f"\n{filepath}:")
            all_warnings.extend(f"  {w}" for w in warnings)

    if all_warnings:
        print("⚠️  Skip/focus markers found:")
        print("\n".join(all_warnings))
        print("\nPlease review:")
        print("  - Remove @pytest.mark.skip before committing")
        print("  - Use @pytest.mark.skipif with conditions")
        print("  - Remove @pytest.mark.focus markers")
        print("\nTo bypass: git commit --no-verify")
        # Exit with 0 to warn but not block
        sys.exit(0)

    print("✓ No skip/focus markers found")
    sys.exit(0)


if __name__ == "__main__":
    main()
