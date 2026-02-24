#!/usr/bin/env python3
"""
Generate Repository Status Card for Zen-AI-Pentest
Updates automatically with each push/commit via GitHub Actions
"""

import os
import subprocess
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont


def run_git_command(cmd):
    """Run git command and return output"""
    try:
        result = subprocess.run(
            cmd, shell=False, capture_output=True, text=True, cwd=os.getcwd()
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"Error running command: {e}")
        return "N/A"


def get_repo_stats():
    """Get repository statistics"""
    stats = {}

    # Total commits
    stats["total_commits"] = run_git_command("git rev-list --count HEAD")

    # Contributors
    contributors = run_git_command("git log --format='%an' | sort -u | wc -l")
    stats["contributors"] = contributors

    # Last commit date
    last_commit = run_git_command("git log -1 --format='%cd' --date=short")
    stats["last_commit"] = last_commit

    # Files count
    stats["total_files"] = run_git_command("git ls-files | wc -l")

    # Lines of code
    try:
        loc_result = run_git_command(
            "git ls-files | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}'"
        )
        stats["lines_of_code"] = loc_result
    except Exception:
        stats["lines_of_code"] = "N/A"

    # Branch name
    stats["branch"] = run_git_command("git branch --show-current")

    # Repository age (days since first commit)
    first_commit_date = run_git_command(
        "git log --reverse --format='%cd' --date=short | head -1"
    )
    if first_commit_date != "N/A":
        try:
            first_date = datetime.strptime(first_commit_date, "%Y-%m-%d")
            today = datetime.now()
            age_days = (today - first_date).days
            stats["repo_age_days"] = str(age_days)
            stats["repo_age_display"] = (
                f"{age_days} days"
                if age_days < 365
                else f"{age_days // 365}y {(age_days % 365) // 30}m"
            )
        except Exception:
            stats["repo_age_days"] = "N/A"
            stats["repo_age_display"] = "N/A"
    else:
        stats["repo_age_days"] = "N/A"
        stats["repo_age_display"] = "N/A"

    # Recent commits (last 7 days)
    recent_commits = run_git_command(
        "git log --since='7 days ago' --oneline | wc -l"
    )
    stats["recent_commits"] = recent_commits

    return stats


def get_tool_stats():
    """Count integrated tools"""
    tools_dir = os.path.join(os.getcwd(), "tools")
    tool_count = 0

    if os.path.exists(tools_dir):
        for file in os.listdir(tools_dir):
            if file.endswith("_integration.py"):
                tool_count += 1

    return tool_count


def get_evolution_phase(stats):
    """Determine current evolution phase based on repo stats"""
    try:
        commits = int(stats.get("total_commits", 0))
        if commits < 50:
            return "🌱 Phase 1: Foundation"
        elif commits < 150:
            return "🔧 Phase 2: Real Tools"
        elif commits < 300:
            return "🤖 Phase 3: Multi-Agent"
        elif commits < 500:
            return "🛡️ Phase 4: Security Engine"
        elif commits < 700:
            return "🏢 Phase 5: Enterprise"
        elif commits < 900:
            return "🧠 Phase 6: AI Personas"
        else:
            return "🚀 Phase 7: Mature (v2.3.9)"
    except Exception:
        return "Unknown Phase"


def generate_status_card():
    """Generate the repository status card image"""

    # Get statistics
    stats = get_repo_stats()
    tool_count = get_tool_stats()
    evolution_phase = get_evolution_phase(stats)

    # Image dimensions
    width = 800
    height = 600

    # Colors (dark theme)
    bg_color = (30, 30, 40)
    header_color = (45, 45, 60)
    accent_color = (100, 200, 255)
    text_color = (240, 240, 240)
    secondary_text = (180, 180, 180)
    success_color = (100, 255, 100)
    warning_color = (255, 200, 100)
    border_color = (60, 60, 80)

    # Create image
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Try to load fonts (fallback to default if not available)
    try:
        font_title = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28
        )
        font_header = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18
        )
        font_text = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14
        )
        font_small = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12
        )
    except Exception:
        font_title = ImageFont.load_default()
        font_header = ImageFont.load_default()
        font_text = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Draw border
    draw.rectangle(
        [(10, 10), (width - 10, height - 10)], outline=border_color, width=2
    )

    # Header background
    draw.rectangle(
        [(10, 10), (width - 10, 80)], fill=header_color, outline=border_color
    )

    # Title
    title = "Zen-AI-Pentest Repository Status"
    draw.text(
        (width // 2, 30),
        title,
        fill=accent_color,
        font=font_title,
        anchor="mm",
    )

    # Last updated
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    draw.text(
        (width // 2, 60),
        f"Last Updated: {timestamp}",
        fill=secondary_text,
        font=font_small,
        anchor="mm",
    )

    # Current Evolution Phase
    y_pos = 100
    draw.text(
        (30, y_pos), evolution_phase, fill=success_color, font=font_header
    )
    y_pos += 35

    # Separator line
    draw.line([(30, y_pos), (width - 30, y_pos)], fill=border_color, width=1)
    y_pos += 20

    # Statistics Section
    draw.text(
        (30, y_pos),
        "📊 Repository Statistics",
        fill=accent_color,
        font=font_header,
    )
    y_pos += 30

    # Stats grid
    stats_data = [
        ("📝 Total Commits:", stats.get("total_commits", "N/A")),
        ("👥 Contributors:", stats.get("contributors", "N/A")),
        ("📁 Total Files:", stats.get("total_files", "N/A")),
        ("📏 Lines of Code:", stats.get("lines_of_code", "N/A")),
        ("⏱️ Repository Age:", stats.get("repo_age_display", "N/A")),
        ("🔧 Integrated Tools:", str(tool_count)),
        ("🌿 Branch:", stats.get("branch", "N/A")),
        ("📅 Last Commit:", stats.get("last_commit", "N/A")),
    ]

    col1_x = 50
    col2_x = 250
    row_height = 25

    for i, (label, value) in enumerate(stats_data):
        row = i % 4
        col = i // 4
        x = col1_x if col == 0 else col2_x + 200
        y = y_pos + (row * row_height)

        draw.text((x, y), label, fill=secondary_text, font=font_text)
        draw.text((x + 150, y), value, fill=text_color, font=font_text)

    y_pos += (4 * row_height) + 30

    # Separator line
    draw.line([(30, y_pos), (width - 30, y_pos)], fill=border_color, width=1)
    y_pos += 20

    # Recent Activity
    draw.text(
        (30, y_pos), "📈 Recent Activity", fill=accent_color, font=font_header
    )
    y_pos += 30

    recent = stats.get("recent_commits", "0")
    activity_text = f"Commits in last 7 days: {recent}"
    draw.text((50, y_pos), activity_text, fill=text_color, font=font_text)
    y_pos += 25

    # Activity indicator
    try:
        recent_int = int(recent)
        if recent_int >= 10:
            activity_status = "🔥 Very Active"
            status_color = success_color
        elif recent_int >= 5:
            activity_status = "✅ Active"
            status_color = warning_color
        elif recent_int > 0:
            activity_status = "⚡ Maintained"
            status_color = (255, 255, 100)
        else:
            activity_status = "⏸️ Dormant"
            status_color = secondary_text

        draw.text(
            (50, y_pos),
            f"Status: {activity_status}",
            fill=status_color,
            font=font_text,
        )
    except Exception:
        pass

    y_pos += 40

    # Separator line
    draw.line([(30, y_pos), (width - 30, y_pos)], fill=border_color, width=1)
    y_pos += 20

    # Legal Notice for AI Agents
    draw.text(
        (30, y_pos),
        "⚖️ Legal Notice for AI Agents",
        fill=(255, 100, 100),
        font=font_header,
    )
    y_pos += 30

    legal_lines = [
        "• Only scan systems you OWN or have EXPLICIT WRITTEN permission to test",
        "• Unauthorized scanning is ILLEGAL and can result in criminal prosecution",
        "• The USER is solely responsible for their actions, NOT the AI",
        "• This tool is for authorized security testing and educational purposes only",
    ]

    for line in legal_lines:
        draw.text((50, y_pos), line, fill=secondary_text, font=font_small)
        y_pos += 18

    y_pos += 15

    # Footer
    draw.text(
        (width // 2, height - 25),
        "🤖 Auto-generated by GitHub Actions | Updates on every push",
        fill=secondary_text,
        font=font_small,
        anchor="mm",
    )

    # Save image
    output_dir = os.path.join(os.getcwd(), "docs", "status")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "repo_status_card.png")

    img.save(output_path, "PNG")
    print(f"Status card generated: {output_path}")
    print(f"Evolution Phase: {evolution_phase}")
    print(f"Total Commits: {stats.get('total_commits', 'N/A')}")
    print(f"Tools: {tool_count}")


if __name__ == "__main__":
    generate_status_card()
